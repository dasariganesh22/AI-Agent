import sys
import os
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView

class HologramUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 1. Window Settings: Frameless, Always on Top, and Transparent
        # 1. Window Settings: Frameless, Always on Top, Transparent, AND Click-Through
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.WindowTransparentForInput  # 🔥 THIS IS THE MAGIC FIX
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 2. Setup the Web Engine Browser
        self.browser = QWebEngineView()
        
        # Force the engine to render the HTML transparency correctly
        self.browser.page().setBackgroundColor(Qt.GlobalColor.transparent)
        
        # 3. Load your existing index.html file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(current_dir, "index.html")
        self.browser.load(QUrl.fromLocalFile(html_path))
        
        self.setCentralWidget(self.browser)
        
        # 4. Set initial size
        self.resize(1100, 600)
        self.old_pos = None

    # Enable moving the frameless window by clicking and dragging anywhere
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HologramUI()
    window.show()
    sys.exit(app.exec())