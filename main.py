# main.py
# ──────────────────────────────────────────────────────────────────────
# FlowPy — Görsel Algoritma Yorumlayıcı Motor
# Ana giriş noktası: UI yükleme, sahne bağlama, sinyal/slot kurulumu.
# ──────────────────────────────────────────────────────────────────────

import sys
import os

from PyQt6.QtWidgets import (QApplication, QMainWindow, QFileDialog,
                              QListWidgetItem, QTableWidgetItem, QHeaderView)
from PyQt6 import uic
from PyQt6.QtGui import QAction, QPalette, QColor
from PyQt6.QtCore import Qt

from core.registry import NodeRegistry
from core.interpreter import Interpreter
from core.serializer import FlowSerializer
from core.undo import UndoManager
from core.generator import CodeGenerator
from core.syntax_highlighter import CodeHighlighter
from views.canvas import FlowScene, ZoomPanFilter
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
        
        # ── 3.1 Yakınlaştırma ve Kaydırma filtresi ───────────────────
        self.zoom_pan_filter = ZoomPanFilter(self.graphicsView, self)
        self.graphicsView.viewport().installEventFilter(self.zoom_pan_filter)

        # ── 4. Yorumlayıcıyı oluştur ────────────────────────────────
        self.interpreter = Interpreter(registry=self.registry)

        # ── 5. While düğümünü listeye ekle ───────────────────────────
        self._ensure_node_list_items()

        # ── 6. Sinyal / Slot bağlantıları ────────────────────────────
        #   Interpreter log → konsol
        self.interpreter.log_message.connect(self.consoleOutput.append)

        self._active_edges = []

        #   Interpreter highlight → düğüm & kenar vurgulama
        self.interpreter.highlight_node.connect(self._highlight_node)
        self.interpreter.highlight_edge.connect(self._highlight_edge)
        self.interpreter.clear_highlights.connect(self._clear_all_highlights)
        
        #   Debugger & Watcher sinyalleri
        self.interpreter.scope_changed.connect(self._update_variable_watcher)
        self.interpreter.flow_state_changed.connect(self._update_toolbar_state)

        #   Toolbar Aksiyonları
        self.actionRunFlow.triggered.connect(self.interpreter.run_flow)
        self.actionStepFlow.triggered.connect(self.interpreter.step_flow)
        self.actionStopFlow.triggered.connect(self.interpreter.stop_flow)

        # ── 6.5 Undo / Redo Yönetimi ─────────────────────────────────
        self.undo_manager = UndoManager(self.registry, self.scene)
        self.scene.history_changed.connect(self.undo_manager.save_snapshot)

        #   Sahne seçim değişikliği → özellikler panelini güncelle
        self.scene.selectionChanged.connect(self._update_properties_panel)

        # ── 7. Değişken tablosu başlangıç ayarları ───────────────────
        self.variableTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.variableTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # Başlangıçta Buton Durumları
        self._update_toolbar_state(is_active=False, is_paused=False)

        # ── 7.5 Code Generator Bağlantıları ──────────────────────────
        self.code_generator = CodeGenerator(self.registry)
        self.code_highlighter = CodeHighlighter(self.codeGenOutput.document())
        self.scene.history_changed.connect(self._update_live_generation)
        self.codeGenLangCombo.currentIndexChanged.connect(self._update_live_generation)
        
        # Buton bağlantıları
        self.codeGenCopyBtn.clicked.connect(self._copy_generated_code)
        self.codeGenSaveBtn.clicked.connect(self._export_generated_code)
        
        self._update_live_generation() # İlk açılışta boş/start renderı için

        # ── 8. Dosya menüsü aksiyonları ──────────────────────────────
        self._setup_file_menu()

        # ── 9. Pencere başlığı & durum çubuğu ───────────────────────
        self.setWindowTitle("FlowPy — Görsel Algoritma Yorumlayıcı")
        self.statusbar.showMessage(
            "Hazır — Düğümleri sürükleyin, çift tıklayarak özelleştirin."
        )

    # ── Liste Elemanları ─────────────────────────────────────────────

    def _ensure_node_list_items(self):
        """Eksik olan düğüm türlerini sol panele ekler."""
        existing = []
        for i in range(self.nodeListWidget.count()):
            existing.append(self.nodeListWidget.item(i).text())

        required_nodes = ["While", "Input", "Output", "For", "Function", "Return"]
        for node_type in required_nodes:
            if node_type not in existing:
                self.nodeListWidget.addItem(QListWidgetItem(node_type))

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
        
        self.menuFile.addSeparator()
        
        undo_action = QAction("↩️  Geri Al (Undo)", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo_manager.undo)
        self.menuFile.addAction(undo_action)
        self.addAction(undo_action) # Global shortcut

        redo_action = QAction("↪️  İleri Al (Redo)", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.undo_manager.redo)
        self.menuFile.addAction(redo_action)
        self.addAction(redo_action) # Global shortcut

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

    # ── Vurgulama (Çalıştırma Animasyonu) ─────────────────────

    def _highlight_node(self, node):
        """Çalıştırılan düğümü vurgular."""
        if hasattr(node, "set_highlight"):
            node.set_highlight(True)
        else:
            node._highlight_active = True
            node.update()

    def _highlight_edge(self, edge):
        """Çalıştırılan kenar bağlantısını sahnede yürütür (animasyon)."""
        edge.set_animating(True)
        self._active_edges.append(edge)

    def _clear_all_highlights(self):
        """Tüm düğüm ve kenarların üzerindeki çalıştırma vurgusunu temizler."""
        for item in self.scene.items():
            if isinstance(item, BaseNode):
                if hasattr(item, "set_highlight"):
                    item.set_highlight(False)
                elif item._highlight_active:
                    item._highlight_active = False
                    item.update()
                    
        for edge in self._active_edges:
            edge.set_animating(False)
        self._active_edges.clear()

    # ── Özellikler Paneli Güncelleme ─────────────────────────────────

    def _update_properties_panel(self):
        """Seçili düğümün özelliklerini sağ panele yazar."""
        try:
            selected = self.scene.selectedItems()
        except RuntimeError:
            # Uygulama kapanırken scene silinmiş olabilir
            return

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

    # ── Debugger & Watcher UI ────────────────────────────────────────

    def _update_variable_watcher(self, scope: dict):
        """Çalışan ortamın (scope) değişkenlerini sağ tabloya yansıtır."""
        self.variableTable.setRowCount(0) # Tabloyu temizle
        
        # Sadece built-in olmayan kendi tanımladığımız değerleri göster
        custom_vars = {k: v for k, v in scope.items() if not k.startswith("__")}
        
        self.variableTable.setRowCount(len(custom_vars))
        
        for row, (key, value) in enumerate(custom_vars.items()):
            key_item = QTableWidgetItem(str(key))
            value_item = QTableWidgetItem(str(value))
            
            # Salt okunur yap
            key_item.setFlags(key_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            self.variableTable.setItem(row, 0, key_item)
            self.variableTable.setItem(row, 1, value_item)

    def _update_toolbar_state(self, is_active: bool, is_paused: bool):
        """Toolbar butonlarının Enable/Disable durumlarını ayarlar."""
        if not is_active:
            # Çalışmıyor (Boşta)
            self.actionRunFlow.setEnabled(True)
            self.actionStepFlow.setEnabled(True)
            self.actionStopFlow.setEnabled(False)
            self.actionRunFlow.setText("▶ Run All")
            self.variableTable.setRowCount(0) # Tabloyu sıfırla
        else:
            if is_paused:
                # Duraklatıldı (Step adımında)
                self.actionRunFlow.setEnabled(True)
                self.actionStepFlow.setEnabled(True)
                self.actionStopFlow.setEnabled(True)
                self.actionRunFlow.setText("▶ Continue")
            else:
                # Tam gaz çalışıyor (Pause butonu yapabiliriz ama şimdilik Step kapalı)
                self.actionRunFlow.setEnabled(False)
                self.actionStepFlow.setEnabled(False)
                self.actionStopFlow.setEnabled(True)

    # ── Live Generation ──────────────────────────────────────────────

    def _update_live_generation(self):
        """Graph değiştiğinde veya dil değiştirildiğinde kod panelini yeniler."""
        lang = self.codeGenLangCombo.currentText()
        if not lang:
            return
            
        generated_code = self.code_generator.generate(lang)
        self.codeGenOutput.setPlainText(generated_code)

    def _copy_generated_code(self):
        """Üretilen kodu işletim sistemi panosuna (clipboard) kopyalar."""
        text = self.codeGenOutput.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.statusbar.showMessage("✔ Kod panoya kopyalandı.", 3000)
            
    def _export_generated_code(self):
        """Üretilen kodu seçili dile uygun uzantıyla dışa aktarır."""
        text = self.codeGenOutput.toPlainText()
        if not text:
            self.statusbar.showMessage("⚠ Dışa aktarılacak kod bulunamadı.", 3000)
            return
            
        lang = self.codeGenLangCombo.currentText().lower()
        ext_map = {
            "python": ("Python (*.py)", ".py"),
            "c": ("C Source (*.c)", ".c"),
            "java": ("Java Source (*.java)", ".java"),
            "pseudocode": ("Text File (*.txt)", ".txt")
        }
        
        filter_str, default_ext = ext_map.get(lang, ("Text File (*.txt)", ".txt"))
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, f"Kodu {lang.capitalize()} Olarak Dışa Aktar", f"flow_export{default_ext}", filter_str
        )
        
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(text)
                self.statusbar.showMessage(f"✔ Kod başarıyla dışa aktarıldı: {filepath}", 4000)
            except Exception as e:
                self.statusbar.showMessage(f"❌ Dışa aktarma hatası: {e}", 4000)


def setup_dark_theme(app: QApplication):
    """QApplication için Qt'nin dâhili paletiyle modern koyu tema oluşturur."""
    app.setStyle("Fusion")
    palette = QPalette()
    
    dark_gray = QColor(45, 45, 45)
    text_color = QColor(210, 210, 210)
    
    palette.setColor(QPalette.ColorRole.Window, dark_gray)
    palette.setColor(QPalette.ColorRole.WindowText, text_color)
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, dark_gray)
    palette.setColor(QPalette.ColorRole.ToolTipBase, text_color)
    palette.setColor(QPalette.ColorRole.ToolTipText, text_color)
    palette.setColor(QPalette.ColorRole.Text, text_color)
    palette.setColor(QPalette.ColorRole.Button, dark_gray)
    palette.setColor(QPalette.ColorRole.ButtonText, text_color)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    
    app.setPalette(palette)

# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    setup_dark_theme(app)
    window = FlowPyApp()
    window.show()
    sys.exit(app.exec())