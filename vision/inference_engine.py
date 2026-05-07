import os
import time
import cv2
import numpy as np
from typing import List
from utils.dto import Detection
from utils.config_manager import ConfigManager
from utils.logger import logger

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

try:
    from ultralytics import YOLO as UltralyticsYOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False

CLASS_NAMES = ["Aflatoxin", "Healthy"]


class YOLOONNXEngine:
    """
    Hem .pt (Ultralytics) hem .onnx (onnxruntime) modelini destekler.
    Model dosyası bulunamazsa Demo Modunda çalışır.

    Tahmin akışı:
      1. OpenCV ile frame içindeki her inciri ayrı ayrı tespit et.
      2. Her inciri kırp → kare yap → 640x640'a ölçekle.
      3. Her kırpılmış inciri YOLO'ya gönder.
      4. YOLO sonucunu orijinal frame koordinatlarına geri çevir.
      Bu sayede tepside kaç incir olursa olsun her biri ayrı kutu alır.
    """

    def __init__(
        self,
        model_path: str = None,
        conf_threshold: float = None,
        iou_threshold: float = None,
    ):
        cfg = ConfigManager()
        configured = cfg.get_path("model", "model_path", "models/final_model.pt")
        self._model_path = model_path or configured
        self._conf = (
            conf_threshold
            if conf_threshold is not None
            else cfg.get_float("model", "conf_threshold", 0.50)
        )
        self._iou = (
            iou_threshold
            if iou_threshold is not None
            else cfg.get_float("model", "iou_threshold", 0.45)
        )
        self._input_size = cfg.get_int("model", "input_size", 640)

        self._session = None        # onnxruntime session
        self._pt_model = None       # ultralytics YOLO
        self._demo_mode = False
        self._backend = None        # "onnx" | "pt" | "demo"
        self._input_name = None
        self._rng = np.random.default_rng(42)

        self._load_model()

    # ── Model yükleme ─────────────────────────────────────────────────────

    def _load_model(self):
        if self._try_load(self._model_path):
            return

        base = os.path.splitext(self._model_path)[0]
        for alt_ext in (".pt", ".onnx"):
            alt = base + alt_ext
            if alt != self._model_path and self._try_load(alt):
                return

        self._demo_mode = True
        self._backend = "demo"
        logger.info("Model bulunamadı → Demo modu aktif.")

    def _try_load(self, path: str) -> bool:
        if not os.path.exists(path):
            return False
        ext = os.path.splitext(path)[1].lower()
        if ext == ".pt":
            return self._load_pt(path)
        if ext == ".onnx":
            return self._load_onnx(path)
        return False

    def _load_pt(self, path: str) -> bool:
        if not ULTRALYTICS_AVAILABLE:
            logger.warning(f"ultralytics kurulu değil, {path} yüklenemedi.")
            return False
        try:
            self._pt_model = UltralyticsYOLO(path)
            self._backend = "pt"
            logger.info(f"Ultralytics .pt modeli yüklendi: {path}")
            return True
        except Exception as e:
            logger.error(f".pt yüklenemedi: {e}")
            return False

    def _load_onnx(self, path: str) -> bool:
        if not ONNX_AVAILABLE:
            logger.warning("onnxruntime kurulu değil.")
            return False
        try:
            opts = ort.SessionOptions()
            opts.intra_op_num_threads = 4
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            self._session = ort.InferenceSession(
                path,
                sess_options=opts,
                providers=["CPUExecutionProvider"],
            )
            self._input_name = self._session.get_inputs()[0].name
            self._backend = "onnx"
            logger.info(f"ONNX modeli yüklendi: {path}")
            return True
        except Exception as e:
            logger.error(f"ONNX yüklenemedi: {e}")
            return False

    # ── OpenCV: frame içindeki tüm incirleri bul ──────────────────────────

    def _find_figs(self, frame: np.ndarray):
        """
        Siyah arka plan üzerindeki incir konturlarını döndürür.
        Her eleman: (x, y, w, h) — orijinal frame koordinatlarında.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Otsu: arka plan ile inciri otomatik ayırır
        _, thresh = cv2.threshold(
            blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        kernel = np.ones((5, 5), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        fig_rects = []
        for cnt in contours:
            if cv2.contourArea(cnt) < 2000:
                continue  # toz/gürültü, atla
            fig_rects.append(cv2.boundingRect(cnt))  # (x, y, w, h)

        return fig_rects

    def _crop_and_square(self, frame: np.ndarray, x: int, y: int, w: int, h: int):
        """
        İnciri kırpar, siyah padding ile kare yapar, 640x640'a ölçekler.
        Dönüş: (resized_img, padding_left, padding_top, max_dim)
        """
        cropped = frame[y : y + h, x : x + w]

        max_dim = max(w, h)
        pad_top = (max_dim - h) // 2
        pad_bottom = max_dim - h - pad_top
        pad_left = (max_dim - w) // 2
        pad_right = max_dim - w - pad_left

        squared = cv2.copyMakeBorder(
            cropped,
            pad_top, pad_bottom, pad_left, pad_right,
            cv2.BORDER_CONSTANT,
            value=[0, 0, 0],
        )
        resized = cv2.resize(squared, (640, 640), interpolation=cv2.INTER_AREA)
        return resized, pad_left, pad_top, max_dim

    def _box_to_original(
        self,
        xyxy: list,
        orig_x: int, orig_y: int,
        pad_left: int, pad_top: int,
        max_dim: int,
        frame_w: int, frame_h: int,
    ):
        """
        640x640 üzerindeki YOLO kutu koordinatlarını
        orijinal frame koordinatlarına (normalize) çevirir.
        """
        scale = max_dim / 640.0

        abs_x1 = orig_x - pad_left + xyxy[0] * scale
        abs_y1 = orig_y - pad_top  + xyxy[1] * scale
        abs_x2 = orig_x - pad_left + xyxy[2] * scale
        abs_y2 = orig_y - pad_top  + xyxy[3] * scale

        return [
            max(0.0, abs_x1 / frame_w),
            max(0.0, abs_y1 / frame_h),
            min(1.0, abs_x2 / frame_w),
            min(1.0, abs_y2 / frame_h),
        ]

    # ── Tahmin ────────────────────────────────────────────────────────────

    def predict(self, frame: np.ndarray) -> List[Detection]:
        if self._backend == "pt":
            return self._predict_pt(frame)
        if self._backend == "onnx":
            return self._predict_onnx(frame)
        return self._demo_predict(frame)

    # .pt yolu — her incir için ayrı YOLO çağrısı
    def _predict_pt(self, frame: np.ndarray) -> List[Detection]:
        try:
            frame_h, frame_w = frame.shape[:2]
            detections: List[Detection] = []

            # Adım 1: OpenCV ile tüm incirleri bul
            fig_rects = self._find_figs(frame)

            if not fig_rects:
                logger.debug("Frame'de incir bulunamadı, YOLO atlandı.")
                return []

            # Adım 2: Her incir için ayrı YOLO tahmini
            for (fx, fy, fw, fh) in fig_rects:
                resized, pad_left, pad_top, max_dim = self._crop_and_square(
                    frame, fx, fy, fw, fh
                )

                results = self._pt_model.predict(
                    resized,
                    conf=self._conf,
                    iou=self._iou,
                    imgsz=640,
                    verbose=False,
                )

                for r in results:
                    if r.boxes is None or len(r.boxes) == 0:
                        continue
                    for box in r.boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        xyxy = box.xyxy[0].tolist()

                        # Koordinatları orijinal frame'e geri çevir
                        norm_bbox = self._box_to_original(
                            xyxy,
                            fx, fy,
                            pad_left, pad_top,
                            max_dim,
                            frame_w, frame_h,
                        )

                        detections.append(
                            Detection(
                                class_name=(
                                    CLASS_NAMES[cls_id]
                                    if cls_id < len(CLASS_NAMES)
                                    else "Unknown"
                                ),
                                confidence=conf,
                                bbox=norm_bbox,
                            )
                        )

            return detections

        except Exception as e:
            logger.error(f"PT inference hatası: {e}")
            return []

    # .onnx yolu — manuel preprocess + postprocess (tek frame, eski davranış)
    def _predict_onnx(self, frame: np.ndarray) -> List[Detection]:
        try:
            blob = self._preprocess(frame)
            outputs = self._session.run(None, {self._input_name: blob})
            return self._postprocess(outputs)
        except Exception as e:
            logger.error(f"ONNX inference hatası: {e}")
            return []

    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        img = cv2.resize(frame, (self._input_size, self._input_size))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1))
        return np.expand_dims(img, axis=0)

    def _postprocess(self, outputs: list) -> List[Detection]:
        pred = outputs[0]
        if pred.ndim == 3:
            pred = pred[0].T
        detections = []
        for row in pred:
            scores = row[4:]
            class_id = int(np.argmax(scores))
            conf = float(scores[class_id])
            if conf < self._conf:
                continue
            cx, cy, w, h = row[:4]
            x1 = max(0.0, cx - w / 2) / self._input_size
            y1 = max(0.0, cy - h / 2) / self._input_size
            x2 = min(1.0, cx + w / 2) / self._input_size
            y2 = min(1.0, cy + h / 2) / self._input_size
            detections.append(
                Detection(
                    class_name=(
                        CLASS_NAMES[class_id]
                        if class_id < len(CLASS_NAMES)
                        else "Unknown"
                    ),
                    confidence=conf,
                    bbox=[x1, y1, x2, y2],
                )
            )
        return self._nms(detections)

    def _nms(self, detections: List[Detection]) -> List[Detection]:
        if not detections:
            return []
        boxes = np.array(
            [[d.bbox[0], d.bbox[1], d.bbox[2], d.bbox[3]] for d in detections]
        )
        scores = np.array([d.confidence for d in detections])
        order = scores.argsort()[::-1]
        indices = []
        while order.size > 0:
            i = order[0]
            indices.append(i)
            if order.size == 1:
                break
            xx1 = np.maximum(boxes[i, 0], boxes[order[1:], 0])
            yy1 = np.maximum(boxes[i, 1], boxes[order[1:], 1])
            xx2 = np.minimum(boxes[i, 2], boxes[order[1:], 2])
            yy2 = np.minimum(boxes[i, 3], boxes[order[1:], 3])
            inter = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
            area_i = (boxes[i, 2] - boxes[i, 0]) * (boxes[i, 3] - boxes[i, 1])
            area_o = (
                (boxes[order[1:], 2] - boxes[order[1:], 0])
                * (boxes[order[1:], 3] - boxes[order[1:], 1])
            )
            iou = inter / (area_i + area_o - inter + 1e-6)
            order = order[1:][iou < self._iou]
        return [detections[i] for i in indices]

    # ── Demo modu ─────────────────────────────────────────────────────────

    def _demo_predict(self, frame: np.ndarray) -> List[Detection]:
        """
        Gerçek model olmadan test için:
        ~%12 aflatoksin, ~%55 sağlıklı, ~%33 boş sahne simüle eder.
        """
        time.sleep(0.03)
        roll = self._rng.random()
        if roll < 0.33:
            return []
        elif roll < 0.45:
            conf = float(self._rng.uniform(0.72, 0.97))
            x1 = float(self._rng.uniform(0.10, 0.35))
            y1 = float(self._rng.uniform(0.10, 0.35))
            x2 = float(self._rng.uniform(0.55, 0.85))
            y2 = float(self._rng.uniform(0.55, 0.85))
            return [Detection("Aflatoxin", conf, [x1, y1, x2, y2])]
        else:
            conf = float(self._rng.uniform(0.68, 0.97))
            x1 = float(self._rng.uniform(0.10, 0.35))
            y1 = float(self._rng.uniform(0.10, 0.35))
            x2 = float(self._rng.uniform(0.55, 0.85))
            y2 = float(self._rng.uniform(0.55, 0.85))
            return [Detection("Healthy", conf, [x1, y1, x2, y2])]

    # ── Ayarlar ───────────────────────────────────────────────────────────

    def set_conf_threshold(self, value: float):
        self._conf = value

    @property
    def is_demo_mode(self) -> bool:
        return self._demo_mode

    @property
    def backend(self) -> str:
        return self._backend or "demo"