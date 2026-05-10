# Figion — Aflatoksin Tespit Sistemi

Kuru incirlerde aflatoksin tespiti yapan, UV kamera görüntülerini YOLOv11n (ONNX) ile analiz eden masaüstü uygulaması.

## Gereksinimler

- Python 3.10 veya üzeri
- USB kamera (herhangi bir webcam çalışır)
- UV ışık kaynağı (manuel açılacak — yazılım kontrol etmez)

---

## Kurulum

### Windows
```
setup.bat      # bir kez çalıştır
run.bat        # her seferinde çalıştır
```

### macOS / Linux
```bash
bash setup.sh   # bir kez çalıştır
bash run.sh     # her seferinde çalıştır
```

### Manuel kurulum
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Proje Yapısı

```
figion/
├── main.py                   # Giriş noktası
├── config.ini                # Tüm ayarlar
├── requirements.txt
│
├── vision/
│   ├── camera_manager.py     # OpenCV kamera sarmalayıcısı
│   └── inference_engine.py   # YOLOv11n ONNX motoru
│
├── data/
│   ├── database_handler.py   # SQLite bağlantısı + tablo oluşturma
│   ├── session_dao.py        # Oturum CRUD
│   ├── inspection_repository.py  # İnceleme kayıtları
│   ├── image_archiver.py     # Arka plan görüntü kayıt işçisi
│   └── session_manager.py    # Oturum koordinatörü
│
├── control/
│   ├── hardware_monitor.py   # Donanım sağlık kontrolü
│   └── state_manager.py      # FSM (Hazır/Taranıyor/Hata…)
│
├── ui/
│   ├── main_window.py        # Ana PyQt6 penceresi
│   ├── video_processor_worker.py  # QThread: kamera + AI
│   ├── widgets.py            # Küçük yeniden kullanılabilir widget'lar
│   └── styles.py             # Qt stil sayfası (karanlık tema)
│
├── utils/
│   ├── config_manager.py     # config.ini okuyucu (Singleton)
│   ├── logger.py             # Dosya + konsol loglama
│   ├── path_builder.py       # Dosya yolu oluşturucu
│   └── dto.py                # Veri transfer nesneleri
│
├── models/
│   ├── figion_yolo.onnx      # (buraya koyun)
│   └── README.txt
│
└── data/                     # Otomatik oluşturulur
    ├── figion.db
    ├── images/YYYY-MM-DD/BATCH_ID/
    ├── logs/
    └── exports/
```

---

## Kullanım

1. UV ışığı **elle açın**, incirleri konveyor bandına yerleştirin.
2. Uygulamayı başlatın → **▶ Taramayı Başlat** butonuna tıklayın.
3. Kırmızı kutu = Aflatoksin tespit edildi, Yeşil kutu = Sağlıklı.
4. **■ Taramayı Durdur** → **⬇ CSV Dışa Aktar** ile rapor alın.

---

## Ayarlar (config.ini)

| Bölüm | Anahtar | Varsayılan | Açıklama |
|-------|---------|------------|----------|
| camera | camera_index | 0 | USB kamera numarası (1, 2… deneyin) |
| model | conf_threshold | 0.50 | Minimum güven eşiği |
| model | iou_threshold | 0.45 | NMS IoU eşiği |
| database | db_path | data/figion.db | SQLite dosya yolu |
