# Figion - Aflatoksin Tespit Sistemi

Figion, UV kamera goruntusu uzerinden kuru incirlerde aflatoksin tespiti yapmak icin gelistirilmis bir PyQt6 masaustu uygulamasidir.

Uygulama:
- Canli kameradan goruntu alir
- YOLO tabanli modelle nesne siniflandirmasi yapar
- Sonuclari SQLite veritabanina kaydeder
- Oturum bazli CSV raporu ve goruntu arsivi olusturur

## Ozellikler

- PyQt6 tabanli modern masaustu arayuz
- PT (Ultralytics) ve ONNX (onnxruntime) model destegi
- Model bulunamazsa Demo Modu (simulasyon) ile calisma
- Oturum ve batch yonetimi
- CSV disa aktarma
- Incelenen goruntuleri klasor yapisinda saklama
- Basit donanim durumu kontrolleri ve loglama

## Teknolojiler

- Python 3.10+
- PyQt6
- OpenCV
- NumPy
- onnxruntime
- ultralytics
- SQLite

## Proje Dizini

```text
figionn_2/
|-- main.py
|-- config.ini
|-- requirements.txt
|-- run.bat / run.sh
|-- setup.bat / setup.sh
|-- vision/
|   |-- camera_manager.py
|   `-- inference_engine.py
|-- ui/
|   |-- main_window.py
|   |-- video_processor_worker.py
|   |-- db_viewer.py
|   `-- styles.py
|-- data/
|   |-- database_handler.py
|   |-- session_dao.py
|   |-- inspection_repository.py
|   |-- session_manager.py
|   |-- image_archiver.py
|   |-- images/
|   |-- exports/
|   `-- logs/
|-- control/
|   |-- hardware_monitor.py
|   `-- state_manager.py
|-- utils/
|   |-- config_manager.py
|   |-- logger.py
|   |-- dto.py
|   `-- path_builder.py
`-- models/
        |-- final_model.pt
        `-- final_model.onnx
```

## Kurulum

### 1. Otomatik Kurulum (onerilen)

Windows:

```bat
setup.bat
```

Linux / macOS:

```bash
bash setup.sh
```

Bu adim:
- `venv` olusturur
- Paketleri kurar
- Gerekli klasorleri olusturur (`data/images`, `data/logs`, `data/exports`, `models`)

### 2. Manuel Kurulum

Windows:

```bat
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Linux / macOS:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

## Calistirma

Windows:

```bat
run.bat
```

Not: `run.bat` dosyasi uygulama kapaninca tekrar acar (sonsuz dongu). Tek seferlik calistirma icin `python main.py` kullanabilirsiniz.

Linux / macOS:

```bash
bash run.sh
```

## Model Yapilandirmasi

Model yolu `config.ini` icindeki `model.model_path` alanindan okunur.

Varsayilan:

```ini
[model]
model_path = models/final_model.pt
```

Desteklenen formatlar:
- `.pt` (Ultralytics YOLO)
- `.onnx` (onnxruntime)

Yukleme davranisi:
1. `model_path` dosyasi denenir
2. Bulunamazsa ayni adin `.pt` ve `.onnx` uzantilari denenir
3. Hicbiri bulunamazsa Demo Modu aktif olur

Demo Modu, gercek model dogrulugu yerine test amacli simulasyon ciktisi uretir.

## Kullanim Akisi

1. UV isigi acin ve urunu kamera gorusune alin.
2. Uygulamayi baslatin.
3. `Start Scanning` ile taramayi baslatin.
4. Sonuclari canli ekranda takip edin:
     - `Aflatoxin`: problemli urun
     - `Healthy`: saglikli urun
5. `Stop Scanning` ile oturumu durdurun.
6. `Export CSV` ile oturum raporunu disa alin.

Ek olarak arayuzden:
- Confidence threshold ayarlanabilir
- Veritabani goruntuleyici acilabilir
- Batch bazli yeni oturum baslatilabilir

## Konfigurasyon (config.ini)

Onemli ayarlar:

- `[camera]`
    - `camera_index`: Kullanilacak kamera indeksi (0, 1, 2...)
    - `width`, `height`, `fps`: Kamera parametreleri
- `[model]`
    - `model_path`: Model dosya yolu
    - `conf_threshold`: Guven esigi
    - `iou_threshold`: NMS IoU esigi
    - `input_size`: Model giris boyutu
- `[database]`
    - `db_path`: SQLite dosya yolu
- `[storage]`
    - `images_dir`, `logs_dir`, `exports_dir`
- `[vision]`
    - Stabilite ve aday filtre parametreleri

## Ciktilar

- Veritabani: `data/figion.db`
- Goruntuler: `data/images/<tarih>/<batch_id>/...`
- CSV raporlari: `data/exports/...`
- Loglar: `data/logs/...`

## Sorun Giderme

- Kamera acilmiyorsa:
    - `config.ini` icindeki `camera_index` degerini degistirin
    - Kameranin baska bir uygulama tarafindan kullanilmadigindan emin olun
- Model yuklenmiyorsa:
    - `model.model_path` yolunu kontrol edin
    - Gerekli paketlerin kurulu oldugunu dogrulayin (`onnxruntime`, `ultralytics`)
- Performans dusukse:
    - Kamera cozunurlugunu dusurun (`camera.width`, `camera.height`)
    - `conf_threshold` ve vision parametrelerini ortama gore ayarlayin

## Lisans

Lisans bilgisi icin `LICENSE` dosyasina bakin.
