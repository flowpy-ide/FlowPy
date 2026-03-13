# main.py
# ──────────────────────────────────────────────────────────────────────
# FlowPy — Görsel Algoritma Yorumlayıcı Motor
# Ana giriş noktası: UI yükleme, sahne bağlama, sinyal/slot kurulumu.
# ──────────────────────────────────────────────────────────────────────

import sys
import os

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6 import uic

from core.registry import NodeRegistry
from core.interpreter import Interpreter
from views.canvas import FlowScene


class FlowPyApp(QMainWindow):
    """Ana pencere — UI dosyasını yükler, sahneyi ve yorumlayıcıyı bağlar."""

    def __init__(self):
        super().__init__()

        # ── 1. UI dosyasını yükle ────────────────────────────────────
        ui_path = os.path.join(os.path.dirname(__file__), "views", "mainwindow.ui")
        uic.loadUi(ui_path, self)

        # ── 2. Merkezi kayıt defterini oluştur ──────────────────────
        self.registry = NodeRegistry()

        # ── 3. Sahneyi oluştur ve graphicsView'a bağla ──────────────
        self.scene = FlowScene(registry=self.registry)
        self.graphicsView.setScene(self.scene)
        self.graphicsView.setAcceptDrops(True)

        # ── 4. Yorumlayıcıyı oluştur ────────────────────────────────
        self.interpreter = Interpreter(registry=self.registry)

        # ── 5. Sinyal / Slot bağlantıları ────────────────────────────
        #   Interpreter log sinyali → konsol alanına yaz
        self.interpreter.log_message.connect(self.consoleOutput.append)

        #   Menü: Çalıştır → Akışı Çalıştır  (Ctrl+R)
        self.actionRunFlow.triggered.connect(self.interpreter.run_flow)

        # ── 6. Pencere başlığı & durum çubuğu ───────────────────────
        self.setWindowTitle("FlowPy — Görsel Algoritma Yorumlayıcı")
        self.statusbar.showMessage("Hazır — Düğümleri sol panelden tuvale sürükleyin.")


# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FlowPyApp()
    window.show()
    sys.exit(app.exec())