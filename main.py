# main.py
# ──────────────────────────────────────────────────────────────────────
# FlowPy — Görsel Algoritma Yorumlayıcı Motor
# Ana giriş noktası: UI yükleme, sahne bağlama, sinyal/slot kurulumu.
# ──────────────────────────────────────────────────────────────────────

import sys
import os

from PyQt6.QtWidgets import (QApplication, QMainWindow, QFileDialog,
                              QListWidgetItem)
from PyQt6 import uic
from PyQt6.QtGui import QAction

from core.registry import NodeRegistry
from core.interpreter import Interpreter
from core.serializer import FlowSerializer
from views.canvas import FlowScene
from models.node import BaseNode


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

        # ── 5. While düğümünü listeye ekle ───────────────────────────
        self._ensure_node_list_items()

        # ── 6. Sinyal / Slot bağlantıları ────────────────────────────
        #   Interpreter log → konsol
        self.interpreter.log_message.connect(self.consoleOutput.append)

        #   Interpreter highlight → düğüm vurgulama
        self.interpreter.highlight_node.connect(self._highlight_node)
        self.interpreter.clear_highlights.connect(self._clear_all_highlights)

        #   Menü: Çalıştır → Akışı Çalıştır (Ctrl+R)
        self.actionRunFlow.triggered.connect(self.interpreter.run_flow)

        #   Sahne seçim değişikliği → özellikler panelini güncelle
        self.scene.selectionChanged.connect(self._update_properties_panel)

        # ── 7. Dosya menüsü aksiyonları ──────────────────────────────
        self._setup_file_menu()

        # ── 8. Pencere başlığı & durum çubuğu ───────────────────────
        self.setWindowTitle("FlowPy — Görsel Algoritma Yorumlayıcı")
        self.statusbar.showMessage(
            "Hazır — Düğümleri sürükleyin, çift tıklayarak özelleştirin, "
            "Ctrl+R ile çalıştırın."
        )

    # ── Liste Elemanları ─────────────────────────────────────────────

    def _ensure_node_list_items(self):
        """While düğümü listede yoksa ekler."""
        existing = []
        for i in range(self.nodeListWidget.count()):
            existing.append(self.nodeListWidget.item(i).text())

        if "While" not in existing:
            self.nodeListWidget.addItem(QListWidgetItem("While"))

    # ── Dosya Menüsü ─────────────────────────────────────────────────

    def _setup_file_menu(self):
        """Dosya menüsüne Kaydet / Aç aksiyonlarını ekler."""
        save_action = QAction("💾  Kaydet…", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_flow)
        self.menuFile.addAction(save_action)

        load_action = QAction("📂  Aç…", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self._load_flow)
        self.menuFile.addAction(load_action)

    def _save_flow(self):
        """Akışı JSON dosyasına kaydeder."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Akışı Kaydet", "", "FlowPy Dosyası (*.flowpy);;JSON (*.json)"
        )
        if filepath:
            nodes_count, edges_count = FlowSerializer.save_to_file(
                filepath, self.registry, self.scene
            )
            self.statusbar.showMessage(
                f"✔ Kaydedildi: {nodes_count} düğüm, {edges_count} bağlantı → {filepath}"
            )

    def _load_flow(self):
        """JSON dosyasından akışı yükler."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Akışı Aç", "", "FlowPy Dosyası (*.flowpy);;JSON (*.json)"
        )
        if filepath:
            nodes_count, edges_count = FlowSerializer.load_from_file(
                filepath, self.registry, self.scene
            )
            self.statusbar.showMessage(
                f"✔ Yüklendi: {nodes_count} düğüm, {edges_count} bağlantı ← {filepath}"
            )

    # ── Düğüm Vurgulama (Çalıştırma Animasyonu) ─────────────────────

    def _highlight_node(self, node):
        """Çalıştırılan düğümü vurgular."""
        # Önce tümünün vurgusunu kaldır
        self._clear_all_highlights()
        # Hedef düğümü vurgula
        if hasattr(node, '_highlight_active'):
            node._highlight_active = True
            node.update()

    def _clear_all_highlights(self):
        """Tüm düğümlerin çalıştırma vurgusunu kaldırır."""
        for item in self.scene.items():
            if isinstance(item, BaseNode):
                if item._highlight_active:
                    item._highlight_active = False
                    item.update()

    # ── Özellikler Paneli Güncelleme ─────────────────────────────────

    def _update_properties_panel(self):
        """Seçili düğümün özelliklerini sağ panele yazar."""
        selected = self.scene.selectedItems()
        nodes = [item for item in selected if isinstance(item, BaseNode)]

        if not nodes:
            self.propNodeTitle.setText("Düğüm seçilmedi")
            self.propNodeId.setText("")
            self.propDetails.clear()
            return

        node = nodes[0]
        short_id = node.node_id[:8] if len(node.node_id) >= 8 else node.node_id

        self.propNodeTitle.setText(f"📦  {node.title}")
        self.propNodeId.setText(f"ID: {short_id}…")

        lines = []
        for key, value in node.properties.items():
            display_value = value if value else "(tanımlanmamış)"
            lines.append(f"<b>{key}:</b><br>{display_value}")

        lines.append(f"<br><b>Giriş Portları:</b> {len(node.input_ports)}")
        lines.append(f"<b>Çıkış Portları:</b> {len(node.output_ports)}")
        lines.append(f"<b>Bağlantı Sayısı:</b> {len(node.edges)}")

        self.propDetails.setHtml("<br>".join(lines))


# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FlowPyApp()
    window.show()
    sys.exit(app.exec())