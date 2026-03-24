# main.py
# ──────────────────────────────────────────────────────────────────────
# FlowPy — Modern Algorithm IDE
# Ana giriş noktası: UI yükleme, sahne bağlama, sinyal/slot kurulumu.
# ──────────────────────────────────────────────────────────────────────

import sys
import os

from PyQt6.QtWidgets import (QApplication, QMainWindow, QFileDialog,
                              QTreeWidgetItem, QTableWidgetItem, QHeaderView,
                              QButtonGroup)
from PyQt6 import uic
from PyQt6.QtGui import QAction, QPalette, QColor
from PyQt6.QtCore import Qt

from core.registry import NodeRegistry
from core.interpreter import Interpreter
from core.serializer import FlowSerializer
from core.undo import UndoManager
from core.generator import CodeGenerator
from core.syntax_highlighter import CodeHighlighter
from views.canvas import FlowScene, ZoomPanFilter, HorizontalRuler, VerticalRuler
from models.node import BaseNode


# ── Düğüm Kategori Tanımları ─────────────────────────────────────────
NODE_CATEGORIES = {
    "Basic": [
        ("▶", "Start"),
        ("□", "Process"),
        ("◇", "Decision"),
    ],
    "Flow Control": [
        ("↻", "While"),
        ("⟳", "For"),
    ],
    "I/O": [
        ("⌨", "Input"),
        ("📺", "Output"),
    ],
    "Functions": [
        ("ƒ", "Function"),
        ("↩", "Return"),
    ],
}

# Renk swatchları için düğüm renk eşlemesi
SWATCH_COLORS = [
    ("#ffffff", "White"),
    ("#2ecc71", "Green"),
    ("#a8ff3e", "Lime"),
    ("#00bcd4", "Cyan"),
    ("#3498db", "Blue"),
    ("#9b59b6", "Purple"),
    ("#e91e8c", "Pink"),
    ("#e74c3c", "Red"),
]


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

        # ── 3.2 Cetvelleri bağla ─────────────────────────────────────
        self._setup_rulers()

        # ── 4. Yorumlayıcıyı oluştur ────────────────────────────────
        self.interpreter = Interpreter(registry=self.registry)

        # ── 5. Node Tree (kategorili) ────────────────────────────────
        self._setup_node_tree()

        # ── 6. Sinyal / Slot bağlantıları ────────────────────────────
        self.interpreter.log_message.connect(self.consoleOutput.append)
        self._active_edges = []
        self.interpreter.highlight_node.connect(self._highlight_node)
        self.interpreter.highlight_edge.connect(self._highlight_edge)
        self.interpreter.clear_highlights.connect(self._clear_all_highlights)
        self.interpreter.scope_changed.connect(self._update_variable_watcher)
        self.interpreter.flow_state_changed.connect(self._update_toolbar_state)

        # Toolbar
        self.actionRunFlow.triggered.connect(self.interpreter.run_flow)
        self.actionStepFlow.triggered.connect(self.interpreter.step_flow)
        self.actionStopFlow.triggered.connect(self.interpreter.stop_flow)

        # ── 6.5 Undo / Redo ─────────────────────────────────────────
        self.undo_manager = UndoManager(self.registry, self.scene)
        self.scene.history_changed.connect(self.undo_manager.save_snapshot)
        self.scene.selectionChanged.connect(self._update_properties_panel)
        self.scene.selectionChanged.connect(self._update_style_panel)

        # ── 7. Değişken tablosu ──────────────────────────────────────
        self.variableTable.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch)
        self.variableTable.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        self._update_toolbar_state(is_active=False, is_paused=False)

        # ── 7.5 Code Generator ────────────────────────────────────────
        self.code_generator = CodeGenerator(self.registry)
        self.code_highlighter = CodeHighlighter(self.codeGenOutput.document())
        self.scene.history_changed.connect(self._update_live_generation)
        self.codeGenLangCombo.currentIndexChanged.connect(self._update_live_generation)
        self.codeGenCopyBtn.clicked.connect(self._copy_generated_code)
        self.codeGenSaveBtn.clicked.connect(self._export_generated_code)
        self._update_live_generation()

        # ── 8. Dosya menüsü ──────────────────────────────────────────
        self._setup_file_menu()

        # ── 9. Node arama çubuğu ─────────────────────────────────────
        self.nodeSearchBar.textChanged.connect(self._filter_node_tree)

        # ── 10. Style Customizer bağlantıları ─────────────────────────
        self._setup_style_customizer()

        # ── 11. Zoom Bar bağlantıları ────────────────────────────────
        self._setup_zoom_bar()

        # ── 12. Pencere başlığı ──────────────────────────────────────
        self.setWindowTitle("FlowPy — Modern Algorithm IDE")
        self.statusbar.showMessage(
            "Ready — Drag nodes to canvas, double-click to edit."
        )

    # ── Cetvel Kurulumu ──────────────────────────────────────────────

    def _setup_rulers(self):
        """Yatay ve dikey cetvelleri graphicsView ile senkronize eder."""
        # Ruler widget'larını özel sınıflarla değiştir
        h_ruler = HorizontalRuler(self.graphicsView)
        v_ruler = VerticalRuler(self.graphicsView)

        # canvasWrapper içindeki layout'ta placeholder widgetların yerine koy
        h_layout = self.canvasColLayout
        v_layout = self.canvasRowLayout

        # Önce eski placeholder'ları kaldır
        old_h = self.rulerHorizontal
        old_v = self.rulerVertical

        h_idx = h_layout.indexOf(old_h)
        v_idx = v_layout.indexOf(old_v)

        h_layout.removeWidget(old_h)
        old_h.deleteLater()
        h_layout.insertWidget(h_idx, h_ruler)

        v_layout.removeWidget(old_v)
        old_v.deleteLater()
        v_layout.insertWidget(v_idx, v_ruler)

        self.rulerHorizontal = h_ruler
        self.rulerVertical = v_ruler

        # Scroll değişince cetvelleri yenile
        self.graphicsView.horizontalScrollBar().valueChanged.connect(
            h_ruler.update)
        self.graphicsView.verticalScrollBar().valueChanged.connect(
            v_ruler.update)

    # ── Node Tree Kurulumu ───────────────────────────────────────────

    def _setup_node_tree(self):
        """Kategorili node ağacını oluşturur."""
        self.nodeTreeWidget.clear()
        for category, nodes in NODE_CATEGORIES.items():
            cat_item = QTreeWidgetItem(self.nodeTreeWidget, [category])
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
            font = cat_item.font(0)
            font.setBold(True)
            cat_item.setFont(0, font)
            for icon, name in nodes:
                child = QTreeWidgetItem(cat_item, [f"  {icon}  {name}"])
                child.setData(0, Qt.ItemDataRole.UserRole, name)
                child.setFlags(child.flags() | Qt.ItemFlag.ItemIsDragEnabled)
            cat_item.setExpanded(True)

    def _filter_node_tree(self, text: str):
        """Arama metnine göre node ağacını filtreler."""
        text = text.lower().strip()
        root = self.nodeTreeWidget.invisibleRootItem()
        for i in range(root.childCount()):
            cat = root.child(i)
            any_visible = False
            for j in range(cat.childCount()):
                child = cat.child(j)
                node_name = (child.data(0, Qt.ItemDataRole.UserRole) or "").lower()
                label = child.text(0).lower()
                visible = not text or text in node_name or text in label
                child.setHidden(not visible)
                if visible:
                    any_visible = True
            cat.setHidden(not any_visible and bool(text))
            if any_visible:
                cat.setExpanded(True)

    # ── Style Customizer ─────────────────────────────────────────────

    def _setup_style_customizer(self):
        """Style Customizer panel bağlantılarını kurar."""
        # Opacity slider
        self.opacitySlider.valueChanged.connect(self._on_opacity_changed)

        # Border style
        self.borderStyleCombo.currentIndexChanged.connect(self._on_border_style_changed)

        # Line style
        self.lineStyleCombo.currentIndexChanged.connect(self._on_line_style_changed)

        # Color swatches
        swatch_names = ["colorSwatch0", "colorSwatch1", "colorSwatch2",
                        "colorSwatch3", "colorSwatch4", "colorSwatch5",
                        "colorSwatch6", "colorSwatch7"]
        for i, name in enumerate(swatch_names):
            btn = getattr(self, name, None)
            if btn:
                color = SWATCH_COLORS[i][0]
                btn.clicked.connect(
                    lambda checked, c=color: self._apply_node_color(c))

        # Panel başlangıçta kilitle (seçim yokken)
        self._set_style_panel_enabled(False)

    def _set_style_panel_enabled(self, enabled: bool):
        """Style Customizer kontrollerini etkinleştirir/devre dışı bırakır."""
        for w in [self.opacitySlider, self.borderStyleCombo,
                  self.lineStyleCombo, self.alignLeftBtn, self.alignDiagBtn,
                  self.alignBoxBtn, self.alignCenterBtn, self.alignRightBtn,
                  self.alignJustifyBtn]:
            w.setEnabled(enabled)

        for i in range(8):
            btn = getattr(self, f"colorSwatch{i}", None)
            if btn:
                btn.setEnabled(enabled)

    def _update_style_panel(self):
        """Seçili düğüme göre style panelini günceller."""
        try:
            selected = self.scene.selectedItems()
        except RuntimeError:
            return

        nodes = [item for item in selected if isinstance(item, BaseNode)]

        if not nodes:
            self._set_style_panel_enabled(False)
            # Varsayılan değerlere dön
            self.opacitySlider.blockSignals(True)
            self.opacitySlider.setValue(100)
            self.opacitySlider.blockSignals(False)
            self.opacityValueLabel.setText("100")
            return

        self._set_style_panel_enabled(True)
        node = nodes[0]

        # Mevcut opacity değerini yükle
        current_opacity = int(node.opacity() * 100)
        self.opacitySlider.blockSignals(True)
        self.opacitySlider.setValue(current_opacity)
        self.opacitySlider.blockSignals(False)
        self.opacityValueLabel.setText(str(current_opacity))

        # Border/Line style
        border_idx = getattr(node, "_custom_border_style", 0)
        line_idx = getattr(node, "_custom_line_style", 0)
        self.borderStyleCombo.blockSignals(True)
        self.lineStyleCombo.blockSignals(True)
        self.borderStyleCombo.setCurrentIndex(border_idx)
        self.lineStyleCombo.setCurrentIndex(line_idx)
        self.borderStyleCombo.blockSignals(False)
        self.lineStyleCombo.blockSignals(False)

    def _on_opacity_changed(self, value: int):
        """Seçili düğümlerin opaklığını günceller."""
        self.opacityValueLabel.setText(str(value))
        for item in self.scene.selectedItems():
            if isinstance(item, BaseNode):
                item.setOpacity(value / 100.0)

    def _on_border_style_changed(self, index: int):
        """Seçili düğümlerin kenar stilini günceller."""
        from PyQt6.QtCore import Qt as QtCore
        style_map = {
            0: Qt.PenStyle.SolidLine,
            1: Qt.PenStyle.DashLine,
            2: Qt.PenStyle.DotLine,
            3: Qt.PenStyle.NoPen,
        }
        style = style_map.get(index, Qt.PenStyle.SolidLine)
        for item in self.scene.selectedItems():
            if isinstance(item, BaseNode):
                item._custom_border_style = index
                item._border_pen_style = style
                item.update()

    def _on_line_style_changed(self, index: int):
        """Seçili düğümlerin çizgi stilini günceller."""
        style_map = {
            0: Qt.PenStyle.SolidLine,
            1: Qt.PenStyle.DashLine,
            2: Qt.PenStyle.DotLine,
        }
        style = style_map.get(index, Qt.PenStyle.SolidLine)
        for item in self.scene.selectedItems():
            if isinstance(item, BaseNode):
                item._custom_line_style = index
                item._line_pen_style = style
                item.update()

    def _apply_node_color(self, hex_color: str):
        """Seçili düğümlere renk uygular."""
        for item in self.scene.selectedItems():
            if isinstance(item, BaseNode):
                item._custom_color = hex_color
                item.update()

    # ── Zoom Bar ─────────────────────────────────────────────────────

    def _setup_zoom_bar(self):
        """Alt zoom barının sinyal bağlantılarını kurar."""
        self._zoom_level = 1.0
        self.zoomInBtn.clicked.connect(self._zoom_in)
        self.zoomOutBtn.clicked.connect(self._zoom_out)

        # Pan mode toggle
        self.panModeBtn.toggled.connect(self._toggle_pan_mode)

        # Page tabs (tek sahne, simüle edilmiş sekmeler)
        page_group = QButtonGroup(self)
        page_group.addButton(self.pageTab1Btn)
        page_group.addButton(self.pageTab2Btn)
        page_group.setExclusive(True)

    def _zoom_in(self):
        factor = 1.2
        self._zoom_level *= factor
        self._zoom_level = min(self._zoom_level, 5.0)
        self.graphicsView.scale(factor, factor)
        self._update_zoom_label()

    def _zoom_out(self):
        factor = 1.0 / 1.2
        self._zoom_level *= factor
        self._zoom_level = max(self._zoom_level, 0.1)
        self.graphicsView.scale(factor, factor)
        self._update_zoom_label()

    def _update_zoom_label(self):
        self.zoomLabel.setText(f"{int(self._zoom_level * 100)}%")
        # Ruler'ları yenile
        if hasattr(self, 'rulerHorizontal'):
            self.rulerHorizontal.update()
        if hasattr(self, 'rulerVertical'):
            self.rulerVertical.update()

    def _toggle_pan_mode(self, active: bool):
        from PyQt6.QtWidgets import QGraphicsView
        if active:
            self.graphicsView.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        else:
            self.graphicsView.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

    # ── Dosya Menüsü ─────────────────────────────────────────────────

    def _setup_file_menu(self):
        save_action = QAction("💾  Save…", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_flow)
        self.menuFile.addAction(save_action)

        load_action = QAction("📂  Open…", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self._load_flow)
        self.menuFile.addAction(load_action)

        self.menuFile.addSeparator()

        undo_action = QAction("↩️  Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo_manager.undo)
        self.menuFile.addAction(undo_action)
        self.addAction(undo_action)

        redo_action = QAction("↪️  Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.undo_manager.redo)
        self.menuFile.addAction(redo_action)
        self.addAction(redo_action)

    def _save_flow(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Flow", "", "FlowPy File (*.flowpy);;JSON (*.json)"
        )
        if filepath:
            nodes_count, edges_count = FlowSerializer.save_to_file(
                filepath, self.registry, self.scene
            )
            self.statusbar.showMessage(
                f"✔ Saved: {nodes_count} nodes, {edges_count} edges → {filepath}"
            )

    def _load_flow(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Flow", "", "FlowPy File (*.flowpy);;JSON (*.json)"
        )
        if filepath:
            nodes_count, edges_count = FlowSerializer.load_from_file(
                filepath, self.registry, self.scene
            )
            self.statusbar.showMessage(
                f"✔ Loaded: {nodes_count} nodes, {edges_count} edges ← {filepath}"
            )

    # ── Vurgulama ─────────────────────────────────────────────────────

    def _highlight_node(self, node):
        if hasattr(node, "set_highlight"):
            node.set_highlight(True)
        else:
            node._highlight_active = True
            node.update()

    def _highlight_edge(self, edge):
        edge.set_animating(True)
        self._active_edges.append(edge)

    def _clear_all_highlights(self):
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

    # ── Özellikler Paneli ─────────────────────────────────────────────

    def _update_properties_panel(self):
        try:
            selected = self.scene.selectedItems()
        except RuntimeError:
            return

        nodes = [item for item in selected if isinstance(item, BaseNode)]

        if not nodes:
            self.propNodeTitle.setText("No Node Selected")
            self.propNodeId.setText("")
            self.propDetails.clear()
            return

        node = nodes[0]
        short_id = node.node_id[:8] if len(node.node_id) >= 8 else node.node_id

        self.propNodeTitle.setText(f"📦  {node.title}")
        self.propNodeId.setText(f"ID: {short_id}…")

        lines = []
        for key, value in node.properties.items():
            display_value = value if value else "(unset)"
            lines.append(f"<b>{key}:</b><br>{display_value}")

        lines.append(f"<br><b>Input Ports:</b> {len(node.input_ports)}")
        lines.append(f"<b>Output Ports:</b> {len(node.output_ports)}")
        lines.append(f"<b>Connections:</b> {len(node.edges)}")

        self.propDetails.setHtml("<br>".join(lines))

    # ── Değişken Watcher ─────────────────────────────────────────────

    def _update_variable_watcher(self, scope: dict):
        self.variableTable.setRowCount(0)
        custom_vars = {k: v for k, v in scope.items() if not k.startswith("__")}
        self.variableTable.setRowCount(len(custom_vars))
        for row, (key, value) in enumerate(custom_vars.items()):
            key_item = QTableWidgetItem(str(key))
            value_item = QTableWidgetItem(str(value))
            key_item.setFlags(key_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.variableTable.setItem(row, 0, key_item)
            self.variableTable.setItem(row, 1, value_item)

    # ── Toolbar State ─────────────────────────────────────────────────

    def _update_toolbar_state(self, is_active: bool, is_paused: bool):
        if not is_active:
            self.actionRunFlow.setEnabled(True)
            self.actionStepFlow.setEnabled(True)
            self.actionStopFlow.setEnabled(False)
            self.actionRunFlow.setText("▶ Run All")
            self.variableTable.setRowCount(0)
        else:
            if is_paused:
                self.actionRunFlow.setEnabled(True)
                self.actionStepFlow.setEnabled(True)
                self.actionStopFlow.setEnabled(True)
                self.actionRunFlow.setText("▶ Continue")
            else:
                self.actionRunFlow.setEnabled(False)
                self.actionStepFlow.setEnabled(False)
                self.actionStopFlow.setEnabled(True)

    # ── Live Code Generation ──────────────────────────────────────────

    def _update_live_generation(self):
        lang = self.codeGenLangCombo.currentText()
        if not lang:
            return
        generated_code = self.code_generator.generate(lang)
        self.codeGenOutput.setPlainText(generated_code)

    def _copy_generated_code(self):
        text = self.codeGenOutput.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.statusbar.showMessage("✔ Code copied to clipboard.", 3000)

    def _export_generated_code(self):
        text = self.codeGenOutput.toPlainText()
        if not text:
            self.statusbar.showMessage("⚠ No code to export.", 3000)
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
            self, f"Export as {lang.capitalize()}",
            f"flow_export{default_ext}", filter_str
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(text)
                self.statusbar.showMessage(
                    f"✔ Exported: {filepath}", 4000)
            except Exception as e:
                self.statusbar.showMessage(f"❌ Export error: {e}", 4000)


# ── Tema Kurulumu ─────────────────────────────────────────────────────

def setup_dark_theme(app: QApplication):
    """Modern koyu tema — Fusion palette + global stylesheet."""
    app.setStyle("Fusion")
    palette = QPalette()

    bg = QColor(30, 30, 30)
    panel = QColor(40, 40, 40)
    text = QColor(220, 220, 220)
    accent = QColor(64, 120, 210)
    highlight = QColor(55, 110, 200)

    palette.setColor(QPalette.ColorRole.Window, bg)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, QColor(22, 22, 22))
    palette.setColor(QPalette.ColorRole.AlternateBase, panel)
    palette.setColor(QPalette.ColorRole.ToolTipBase, text)
    palette.setColor(QPalette.ColorRole.ToolTipText, text)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, panel)
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, accent)
    palette.setColor(QPalette.ColorRole.Highlight, highlight)
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    app.setPalette(palette)

    app.setStyleSheet("""
        /* ── Global ── */
        QMainWindow, QWidget {
            font-family: "Segoe UI", sans-serif;
            font-size: 11px;
        }

        /* ── Menu Bar ── */
        QMenuBar {
            background-color: #1e1e1e;
            color: #ddd;
            border-bottom: 1px solid #333;
            padding: 2px 4px;
        }
        QMenuBar::item:selected { background: #3c5a8a; border-radius: 4px; }
        QMenu {
            background-color: #2a2a2a;
            color: #ddd;
            border: 1px solid #444;
        }
        QMenu::item:selected { background: #3c5a8a; }

        /* ── Toolbar ── */
        QToolBar {
            background-color: #252525;
            border-bottom: 1px solid #3a3a3a;
            padding: 3px 6px;
            spacing: 6px;
        }
        QToolBar QToolButton {
            color: #ddd;
            background: #333;
            border: 1px solid #4a4a4a;
            border-radius: 5px;
            padding: 4px 10px;
            font-weight: bold;
        }
        QToolBar QToolButton:hover { background: #3c5a8a; border-color: #5a80c0; }
        QToolBar QToolButton:pressed { background: #2a4070; }
        QToolBar QToolButton:disabled { color: #666; background: #2a2a2a; }

        /* ── Dock Widgets ── */
        QDockWidget {
            color: #ccc;
            font-weight: bold;
            titlebar-close-icon: none;
        }
        QDockWidget::title {
            background: #2a2a2a;
            border-bottom: 2px solid #4078c8;
            padding: 4px 8px;
            text-align: left;
        }

        /* ── Tab Widget ── */
        QTabWidget::pane {
            border: 1px solid #3a3a3a;
            background: #252525;
        }
        QTabBar::tab {
            background: #222;
            color: #aaa;
            border: 1px solid #3a3a3a;
            border-bottom: none;
            padding: 5px 12px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background: #2e2e2e;
            color: #fff;
            border-top: 2px solid #4078c8;
        }
        QTabBar::tab:hover:!selected { background: #2a2a2a; color: #ddd; }

        /* ── Tree Widget (Node Palette) ── */
        QTreeWidget {
            background-color: #1e1e1e;
            color: #ccc;
            border: none;
            alternate-background-color: #232323;
        }
        QTreeWidget::item {
            padding: 3px 2px;
            border-radius: 3px;
        }
        QTreeWidget::item:hover { background: #2c3e5a; }
        QTreeWidget::item:selected { background: #3c5a8a; color: #fff; }

        /* ── Search bar ── */
        QLineEdit {
            background: #1a2030;
            color: #ddd;
            border: 1px solid #3a4a6a;
            border-radius: 6px;
            padding: 4px 8px;
        }
        QLineEdit:focus { border-color: #4078c8; }

        /* ── Tables & Text ── */
        QTableWidget {
            background: #1e1e1e;
            color: #ccc;
            gridline-color: #333;
            border: none;
        }
        QHeaderView::section {
            background: #2a2a2a;
            color: #bbb;
            border: none;
            padding: 4px;
            border-right: 1px solid #333;
        }
        QTextEdit, QTextBrowser {
            background: #1a1a1a;
            color: #ccc;
            border: 1px solid #333;
            border-radius: 4px;
        }
        QScrollBar:vertical {
            background: #1e1e1e;
            width: 8px;
        }
        QScrollBar::handle:vertical { background: #444; border-radius: 4px; }
        QScrollBar:horizontal {
            background: #1e1e1e;
            height: 8px;
        }
        QScrollBar::handle:horizontal { background: #444; border-radius: 4px; }

        /* ── Combo Box ── */
        QComboBox {
            background: #2a2a2a;
            color: #ddd;
            border: 1px solid #4a4a4a;
            border-radius: 4px;
            padding: 3px 8px;
        }
        QComboBox::drop-down { border: none; }
        QComboBox QAbstractItemView {
            background: #2a2a2a;
            color: #ddd;
            selection-background-color: #3c5a8a;
        }

        /* ── Sliders ── */
        QSlider::groove:horizontal {
            background: #333;
            height: 4px;
            border-radius: 2px;
        }
        QSlider::handle:horizontal {
            background: #4078c8;
            width: 14px;
            height: 14px;
            margin: -5px 0;
            border-radius: 7px;
        }
        QSlider::sub-page:horizontal { background: #4078c8; border-radius: 2px; }

        /* ── Bottom Bar ── */
        #bottomBar {
            background: #1e1e1e;
            border-top: 1px solid #333;
        }
        #bottomBar QPushButton {
            background: #2a2a2a;
            color: #ccc;
            border: 1px solid #3a3a3a;
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 11px;
        }
        #bottomBar QPushButton:hover { background: #333; }
        #bottomBar QPushButton:checked {
            background: #3c5a8a;
            color: #fff;
            border-color: #4078c8;
        }
        #bottomBar QLabel {
            color: #aaa;
            font-size: 11px;
        }

        /* ── Status Bar ── */
        QStatusBar {
            background: #1a1a1a;
            color: #888;
            border-top: 1px solid #2a2a2a;
            font-size: 10px;
        }

        /* ── Push Buttons (general) ── */
        QPushButton {
            background: #2d2d2d;
            color: #ccc;
            border: 1px solid #444;
            border-radius: 4px;
            padding: 4px 10px;
        }
        QPushButton:hover { background: #363636; border-color: #5a7ac0; }
        QPushButton:pressed { background: #222; }
        QPushButton:disabled { color: #555; background: #222; border-color: #333; }
    """)


# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    setup_dark_theme(app)
    window = FlowPyApp()
    window.show()
    sys.exit(app.exec())