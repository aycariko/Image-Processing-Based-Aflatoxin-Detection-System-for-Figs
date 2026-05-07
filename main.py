import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QSplashScreen, QLabel
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QLinearGradient, QGradient

from ui.main_window import MainWindow
from utils.logger import logger


# ── Splash screen ──────────────────────────────────────────────────────────
def _make_splash_pixmap(w: int = 520, h: int = 300) -> QPixmap:
    """Programatik olarak oluşturulmuş splash ekranı."""
    pix = QPixmap(w, h)
    pix.fill(QColor("#141414"))

    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # Arka plan ince border
    p.setPen(QColor("#2a2a2a"))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(1, 1, w - 2, h - 2, 12, 12)

    # Üst yeşil aksent çizgisi
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#1D9E75"))
    p.drawRoundedRect(0, 0, w, 4, 2, 2)

    # Logo dairesi
    cx, cy, r = w // 2, 110, 46
    p.setBrush(QColor("#1a2e25"))
    p.setPen(QColor("#1D9E75"))
    p.drawEllipse(cx - r, cy - r, r * 2, r * 2)

    # Logo içi "F" harfi
    f = QFont("Segoe UI", 36, QFont.Weight.Bold)
    p.setFont(f)
    p.setPen(QColor("#1D9E75"))
    p.drawText(cx - 13, cy + 14, "F")

    # Uygulama adı
    f2 = QFont("Segoe UI", 22, QFont.Weight.Normal)
    p.setFont(f2)
    p.setPen(QColor("#e8e8e8"))
    p.drawText(0, 185, w, 36, Qt.AlignmentFlag.AlignHCenter, "Figion")

    # Alt başlık
    f3 = QFont("Segoe UI", 11)
    p.setFont(f3)
    p.setPen(QColor("#555"))
    p.drawText(0, 220, w, 24, Qt.AlignmentFlag.AlignHCenter,
               "Aflatoksin Tespit Sistemi  ·  v1.0")

    # Yükleniyor çubuğu arka plan
    bar_x, bar_y, bar_w, bar_h = w // 2 - 100, 264, 200, 4
    p.setBrush(QColor("#252525"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(bar_x, bar_y, bar_w, bar_h, 2, 2)

    # Yükleniyor çubuğu dolgu
    p.setBrush(QColor("#1D9E75"))
    p.drawRoundedRect(bar_x, bar_y, bar_w // 2, bar_h, 2, 2)

    # Alt not
    f4 = QFont("Segoe UI", 9)
    p.setFont(f4)
    p.setPen(QColor("#333"))
    p.drawText(0, 282, w, 16, Qt.AlignmentFlag.AlignHCenter,
               "TED University  ·  Computer Engineering")

    p.end()
    return pix


# ── Ana giriş noktası ──────────────────────────────────────────────────────
def main():
    for d in ("data/images", "data/logs", "data/exports", "models"):
        os.makedirs(d, exist_ok=True)

    app = QApplication(sys.argv)
    app.setApplicationName("Figion")
    app.setApplicationVersion("1.0.0")
    # app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    # Karanlık tema paleti
    from PyQt6.QtGui import QPalette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor("#1a1a1a"))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor("#e8e8e8"))
    palette.setColor(QPalette.ColorRole.Base,            QColor("#141414"))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor("#1e1e1e"))
    palette.setColor(QPalette.ColorRole.Text,            QColor("#e8e8e8"))
    palette.setColor(QPalette.ColorRole.Button,          QColor("#252525"))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor("#e8e8e8"))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor("#1D9E75"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    # Splash ekranı
    splash_pix = _make_splash_pixmap()
    splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)
    splash.setWindowFlag(Qt.WindowType.FramelessWindowHint)
    splash.show()
    app.processEvents()

    # Model / DB yüklenirken kısa bekleme (gerçekçi his)
    logger.info("Figion başlatılıyor…")
    time.sleep(0.8)
    app.processEvents()

    # Ana pencere
    window = MainWindow()

    # Splash kapat, pencereyi tam ekran aç
    splash.finish(window)
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
