Bu klasöre YOLOv11n ONNX model dosyanızı koyun.

Beklenen dosya adı: figion_yolo.onnx
(config.ini içindeki model_path ayarıyla değiştirilebilir)

--- Model nasıl eğitilir / elde edilir? ---

1. Ultralytics ile kendi modelinizi eğitin:
   pip install ultralytics
   yolo train data=incir.yaml model=yolo11n.pt epochs=100 imgsz=640

2. ONNX formatına çevirin:
   yolo export model=runs/detect/train/weights/best.pt format=onnx

3. Çıkan best.onnx dosyasını buraya kopyalayıp
   figion_yolo.onnx olarak yeniden adlandırın.

Model bulunamazsa uygulama otomatik olarak DEMO modunda çalışır.
Demo modunda ~%%12 aflatoksin oranıyla rastgele sonuçlar üretilir.
