# main.py
# ──────────────────────────────────────────────────────────────────────
# FlowPy — Modern Algorithm IDE
# Ana giriş noktası: UI yükleme, sahne bağlama, sinyal/slot kurulumu.
# ──────────────────────────────────────────────────────────────────────

import sys
import os
import ctypes

from PyQt6.QtWidgets import (QApplication, QMainWindow, QFileDialog,
                              QTreeWidgetItem, QTableWidgetItem, QHeaderView,
                              QButtonGroup, QToolButton, QSlider, QLabel,
                              QWidget, QHBoxLayout, QMessageBox, QInputDialog,
                              QDialog, QVBoxLayout, QLineEdit, QPushButton)
from PyQt6 import uic
from PyQt6.QtGui import (QAction, QIcon, QPalette, QColor, QPainter, QPixmap, QFont)
from PyQt6.QtCore import QPointF, Qt, QTimer, QEvent

from core.registry import NodeRegistry
from core.settings_manager import SettingsManager
from core.i18n import t
from core.interpreter import Interpreter
from core.serializer import FlowSerializer
from core.undo import UndoManager
from core.generator import CodeGenerator
from core.syntax_highlighter import CodeHighlighter
from views.canvas import FlowScene, ZoomPanFilter, HorizontalRuler, VerticalRuler
from views.variable_chart import VariableSparklinePanel
from views.minimap import FlowMinimap
from views.node_tooltip import NodeDocTooltip
from models.node import BaseNode
from core.templates import TEMPLATES, load_template

BASE_DIR = os.path.dirname(__file__)
APP_ICON_PATH = os.path.join(BASE_DIR, "docs", "icon-svg.svg")


# ── Düğüm Kategori Tanımları (isim, renk, ikon şekli) ─────────────────
NODE_CATEGORIES = {
    "Basic": [
        ("Start",    "#22c55e", "rect"),
        ("Process",  "#3b82f6", "rect"),
        ("Decision", "#f59e0b", "diamond"),
    ],
    "Flow Control": [
        ("While", "#8b5cf6", "circle"),
        ("For",   "#8b5cf6", "circle"),
    ],
    "I/O": [
        ("Input",  "#22c55e", "rect"),
        ("Output", "#22c55e", "rect"),
    ],
    "Functions": [
        ("Function", "#ec4899", "rect"),
        ("Return",   "#ec4899", "rect"),
    ],
}


def _make_color_icon(hex_color: str, shape: str = "rect") -> QIcon:
    """16x16 renkli palet ikonu oluşturur."""
    pixmap = QPixmap(16, 16)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(hex_color))
    painter.setPen(Qt.PenStyle.NoPen)
    if shape == "diamond":
        points = [QPointF(8, 1), QPointF(15, 8), QPointF(8, 15), QPointF(1, 8)]
        painter.drawPolygon(points)
    elif shape == "circle":
        painter.drawEllipse(2, 2, 12, 12)
    else:
        painter.drawRoundedRect(2, 2, 12, 12, 3, 3)
    painter.end()
    return QIcon(pixmap)

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
        self.scenes = {
            "page1": FlowScene(registry=self.registry),
            "page2": FlowScene(registry=self.registry)
        }
        self.current_scene = self.scenes["page1"]
        self.graphicsView.setScene(self.current_scene)
        self.graphicsView.setAcceptDrops(True)
        self.graphicsView.installEventFilter(self)

        # ── 3.1 Yakınlaştırma ve Kaydırma filtresi ───────────────────
        self.zoom_pan_filter = ZoomPanFilter(self.graphicsView, self)
        self.graphicsView.viewport().installEventFilter(self.zoom_pan_filter)

        # ── 3.2 Cetvelleri bağla ─────────────────────────────────────
        self._setup_rulers()

        # ── 4. Yorumlayıcıyı oluştur ────────────────────────────────
        self.interpreter = Interpreter(registry=self.registry)

        # ── 5. Node Tree (kategorili) ────────────────────────────────
        self._setup_node_tree()
        self._setup_inspector_badge()
        self._setup_console_output()
        self._setup_toolbar_button_styles()
        self._setup_speed_control()

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
        self.undo_manager = UndoManager(self.registry, self.current_scene)
        self._connect_scene_signals(self.current_scene)

        # ── 7. Değişken tablosu ──────────────────────────────────────
        self.variableTable.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch)
        self.variableTable.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        self.sparkline_panel = VariableSparklinePanel()
        if hasattr(self, "variablesTabLayout"):
            self.variablesTabLayout.addWidget(self.sparkline_panel)
        self.interpreter.scope_changed.connect(self.sparkline_panel.update_scope)
        self._was_flow_active = False
        self._update_toolbar_state(is_active=False, is_paused=False)

        # ── 7.5 Code Generator ────────────────────────────────────────
        self.code_generator = CodeGenerator(self.registry)
        self.code_highlighter = CodeHighlighter(self.codeGenOutput.document())
        self.current_scene.history_changed.connect(self._update_live_generation)
        self.codeGenLangCombo.currentIndexChanged.connect(self._update_live_generation)
        self.codeGenCopyBtn.clicked.connect(self._copy_generated_code)
        self.codeGenSaveBtn.clicked.connect(self._export_generated_code)
        self._update_live_generation()

        # ── 8. Dosya menüsü ──────────────────────────────────────────
        self._setup_file_menu()
        self._setup_edit_menu()
        self._setup_view_menu()

        # ── 9. Node arama çubuğu ─────────────────────────────────────
        self.nodeSearchBar.textChanged.connect(self._filter_node_tree)

        # ── 10. Style Customizer bağlantıları ─────────────────────────
        self._setup_style_customizer()

        # ── 11. Zoom Bar bağlantıları ────────────────────────────────
        self._setup_zoom_bar()

        # ── 11.5 Sayfa durumları (Page-1 / Page-2) ─────────────────
        self._current_page_key = "page1"
        self._page_states = {
            "page1": FlowSerializer.serialize_to_dict(self.registry),
            "page2": {"nodes": [], "edges": []},
        }

        # ── 12. Pencere başlığı ──────────────────────────────────────
        self.setWindowTitle(t("app_title"))
        self.setWindowIcon(QIcon(APP_ICON_PATH))

        self._guided_tour = None
        SettingsManager.instance().ensure_defaults()
        self._node_tooltip = NodeDocTooltip(self)
        self._minimap = FlowMinimap(self.graphicsView, self.current_scene, self.graphicsView)
        self._position_minimap()
        self._minimap.show()
        self._minimap.raise_()

        self._apply_ui_strings()
        self._maybe_show_welcome()

    def _apply_ui_strings(self):
        """Aktif dile göre menü ve panel metinlerini günceller."""
        self.statusbar.showMessage(t("ready_message"))
        self.setWindowTitle(t("app_title"))
        if hasattr(self, "actionRunFlow"):
            self.actionRunFlow.setText(t("run_all"))
        if hasattr(self, "nodePanelDock"):
            self.nodePanelDock.setWindowTitle(t("node_palette"))
        if hasattr(self, "rightPanelDock"):
            self.rightPanelDock.setWindowTitle(t("inspector"))
        if hasattr(self, "consoleDock"):
            self.consoleDock.setWindowTitle(t("console_output"))

    def _maybe_show_welcome(self):
        """İlk açılışta karşılama ekranını gösterir."""
        sm = SettingsManager.instance()
        if not sm.get_bool("show_welcome_on_startup", True):
            QTimer.singleShot(300, self._start_guided_tour)
            return
        if sm.get_bool("welcome_shown", False):
            QTimer.singleShot(300, self._start_guided_tour)
            return

        from views.welcome_screen import FlowPyWelcomeScreen
        dialog = FlowPyWelcomeScreen(self)
        dialog.exec()
        if dialog.load_example:
            self._load_example_flow()
        QTimer.singleShot(300, self._start_guided_tour)

    def _load_example_flow(self):
        """Örnek akış dosyasını yükler (varsa)."""
        path = os.path.join(BASE_DIR, "created_flows", "ornek.flowpy")
        if not os.path.isfile(path):
            return
        FlowSerializer.load_from_file(path, self.registry, self.current_scene)
        self._page_states["page1"] = FlowSerializer.serialize_to_dict(self.registry)
        self.undo_manager._undo_stack.clear()
        self.undo_manager._redo_stack.clear()
        self.undo_manager.save_snapshot()
        self._update_live_generation()
        self.statusbar.showMessage(f"✔ Örnek akış yüklendi.", 4000)

    def _start_guided_tour(self):
        """Eğitim turunu başlatır (ayarlara göre)."""
        sm = SettingsManager.instance()
        if sm.get_bool("tour_completed", False):
            return
        if not sm.get_bool("show_tour_on_startup", True):
            return
        from views.guided_tour import GuidedTour
        if self._guided_tour is None:
            self._guided_tour = GuidedTour(self)
        self._guided_tour.start()

    def _open_settings(self):
        """Ayarlar diyaloğunu açar."""
        from views.settings_dialog import SettingsDialog
        if SettingsDialog(self).exec():
            self._apply_ui_strings()

    def _restart_guided_tour(self):
        """Eğitim turunu sıfırlayıp yeniden başlatır."""
        SettingsManager.instance().set_bool("tour_completed", False)
        from views.guided_tour import GuidedTour
        if self._guided_tour is None:
            self._guided_tour = GuidedTour(self)
        self._guided_tour.restart()

    def _connect_scene_signals(self, scene):
        """Sahne değiştikçe sinyalleri yeni sahneye bağlar."""
        try: scene.history_changed.disconnect()
        except: pass
        try: scene.selectionChanged.disconnect()
        except: pass

        scene.history_changed.connect(self.undo_manager.save_snapshot)
        scene.history_changed.connect(self._update_live_generation)
        scene.selectionChanged.connect(self._update_properties_panel)
        scene.selectionChanged.connect(self._update_style_panel)

    def _switch_page(self, page_key: str):
        """Sayfalar arasında geçiş yapar; her sayfanın akış durumunu ayrı saklar."""
        if page_key == self._current_page_key:
            return

        self._page_states[self._current_page_key] = FlowSerializer.serialize_to_dict(
            self.registry
        )

        target_scene = self.scenes[page_key]
        target_state = self._page_states.get(page_key, {"nodes": [], "edges": []})
        FlowSerializer.deserialize_from_dict(
            target_state, self.registry, target_scene
        )

        self._current_page_key = page_key
        self.current_scene = target_scene
        self.graphicsView.setScene(self.current_scene)
        self.undo_manager.scene = self.current_scene
        self._connect_scene_signals(self.current_scene)
        if hasattr(self, "_minimap"):
            self._minimap.scene = self.current_scene

        self._update_properties_panel()
        self._update_style_panel()
        self._update_variable_watcher({})
        self._update_live_generation()

        self.undo_manager._undo_stack.clear()
        self.undo_manager._redo_stack.clear()
        self.undo_manager.save_snapshot()

        self.statusbar.showMessage(f"Switched to {page_key.capitalize()}.", 2500)

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
            font.setPointSize(9)
            cat_item.setForeground(0, QColor("#555555"))
            cat_item.setFont(0, font)
            for name, color, shape in nodes:
                child = QTreeWidgetItem(cat_item, [f"  {name}"])
                child.setData(0, Qt.ItemDataRole.UserRole, name)
                child.setIcon(0, _make_color_icon(color, shape))
                child.setFlags(child.flags() | Qt.ItemFlag.ItemIsDragEnabled)
            cat_item.setExpanded(True)

    def _setup_console_output(self):
        """Konsol çıktısını HTML loglar için hazırlar."""
        self.consoleOutput.setReadOnly(True)
        self.consoleOutput.setAcceptRichText(True)
        self.consoleOutput.setUndoRedoEnabled(False)
        if hasattr(self, "propDetails"):
            self.propDetails.setUndoRedoEnabled(False)

    def _setup_inspector_badge(self):
        """Inspector panelinde tema uyumlu düğüm rozeti oluşturur."""
        from PyQt6.QtWidgets import QFrame, QVBoxLayout
        layout = self.propertiesTabLayout
        idx = layout.indexOf(self.propNodeTitle)
        self.propNodeBadge = QFrame()
        self.propNodeBadge.setObjectName("propNodeBadge")
        badge_layout = QVBoxLayout(self.propNodeBadge)
        badge_layout.setContentsMargins(8, 8, 8, 8)
        badge_layout.setSpacing(4)
        layout.removeWidget(self.propNodeTitle)
        layout.removeWidget(self.propNodeId)
        badge_layout.addWidget(self.propNodeTitle)
        badge_layout.addWidget(self.propNodeId)
        layout.insertWidget(idx, self.propNodeBadge)

    def _toolbar_button_for_action(self, action: QAction) -> QToolButton | None:
        """Toolbar'daki QAction'a karşılık gelen QToolButton'ı bulur."""
        toolbar = getattr(self, "mainToolBar", None)
        if not toolbar:
            return None
        for btn in toolbar.findChildren(QToolButton):
            if btn.defaultAction() is action:
                return btn
        return None

    def _style_toolbar_action(self, action: QAction, stylesheet: str):
        btn = self._toolbar_button_for_action(action)
        if btn:
            btn.setStyleSheet(stylesheet)

    def _setup_toolbar_button_styles(self):
        """Çalıştırma araç çubuğu butonlarına özel stiller uygular."""
        self._style_toolbar_action(self.actionRunFlow, """
            QToolButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a6b38, stop:1 #0d4022);
                color: #4ade80;
                border: 1px solid #22c55e44;
                border-radius: 6px;
                padding: 5px 14px;
                font-weight: bold;
                font-size: 12px;
            }
            QToolButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #22a050, stop:1 #145c2e);
                border-color: #4ade8066;
            }
            QToolButton:disabled { background: #1a1a1a; color: #333; border-color: #222; }
        """)
        self._style_toolbar_action(self.actionStepFlow, """
            QToolButton {
                background: #1e1e2e;
                color: #a78bfa;
                border: 1px solid #3a1a6e;
                border-radius: 6px;
                padding: 5px 14px;
                font-weight: bold;
            }
            QToolButton:hover { background: #252535; border-color: #8b5cf6; }
            QToolButton:disabled { background: #1a1a1a; color: #333; border-color: #222; }
        """)
        self._style_toolbar_action(self.actionStopFlow, """
            QToolButton {
                background: #1a1a1a;
                color: #444;
                border: 1px solid #2a2a2a;
                border-radius: 6px;
                padding: 5px 14px;
                font-weight: bold;
            }
            QToolButton:enabled {
                background: #2e0d0d;
                color: #f87171;
                border-color: #6e1a1a;
            }
            QToolButton:enabled:hover { background: #3d1010; border-color: #ef4444; }
        """)

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
                btn.setStyleSheet(
                    f"""
                    QPushButton {{
                        background-color: {color};
                        border: 1px solid #4a4a4a;
                        border-radius: 4px;
                    }}
                    QPushButton:hover {{
                        border: 1px solid #f1c40f;
                    }}
                    QPushButton:disabled {{
                        background-color: {color};
                        border: 1px solid #3a3a3a;
                    }}
                    """
                )
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
            selected = self.current_scene.selectedItems()
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
        for item in self.current_scene.selectedItems():
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
        for item in self.current_scene.selectedItems():
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
        for item in self.current_scene.selectedItems():
            if isinstance(item, BaseNode):
                item._custom_line_style = index
                item._line_pen_style = style
                item.update()

    def _apply_node_color(self, hex_color: str):
        """Seçili düğümlere renk uygular."""
        for item in self.current_scene.selectedItems():
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

        # Page tabs
        page_group = QButtonGroup(self)
        page_group.addButton(self.pageTab1Btn)
        page_group.addButton(self.pageTab2Btn)
        page_group.setExclusive(True)
        self.pageTab1Btn.clicked.connect(
            lambda checked: checked and self._switch_page("page1")
        )
        self.pageTab2Btn.clicked.connect(
            lambda checked: checked and self._switch_page("page2")
        )

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

    def _reset_zoom(self):
        """Yakınlaştırmayı %100'e döndürür."""
        current_transform = self.graphicsView.transform().m11()
        if current_transform != 0:
            reset_factor = 1.0 / current_transform
            self.graphicsView.scale(reset_factor, reset_factor)
        self._zoom_level = 1.0
        self._update_zoom_label()

    def _fit_to_flow(self):
        """Tüm akışı görünür alana sığdırır."""
        rect = self.current_scene.itemsBoundingRect()
        if rect.isNull() or rect.isEmpty():
            return
        self.graphicsView.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom_level = self.graphicsView.transform().m11()
        self._update_zoom_label()

    # ── Dosya Menüsü ─────────────────────────────────────────────────

    def _position_minimap(self):
        if hasattr(self, "_minimap"):
            self._minimap.move(
                self.graphicsView.width() - FlowMinimap.WIDTH - 10,
                self.graphicsView.height() - FlowMinimap.HEIGHT - 10,
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_minimap()

    def _setup_speed_control(self):
        """Toolbar'a execution speed slider ekler."""
        speed_widget = QWidget()
        layout = QHBoxLayout(speed_widget)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(6)

        lbl = QLabel("Hız:")
        lbl.setStyleSheet("color: #666; font-size: 11px;")

        self.speedSlider = QSlider(Qt.Orientation.Horizontal)
        self.speedSlider.setRange(0, 10)
        self.speedSlider.setValue(0)
        self.speedSlider.setFixedWidth(90)
        self.speedSlider.setToolTip("Execution hızı: sol=hızlı, sağ=yavaş")
        self.speedSlider.setStyleSheet("""
            QSlider::groove:horizontal { background:#2a2a2a; height:4px; border-radius:2px; }
            QSlider::handle:horizontal {
                background:#4078c8; width:12px; height:12px; margin:-4px 0; border-radius:6px;
            }
            QSlider::sub-page:horizontal { background:#4078c8; border-radius:2px; }
        """)

        self.speedLabel = QLabel("▶▶")
        self.speedLabel.setStyleSheet("color: #4ade80; font-size: 10px; min-width: 24px;")

        layout.addWidget(lbl)
        layout.addWidget(self.speedSlider)
        layout.addWidget(self.speedLabel)

        self.mainToolBar.addSeparator()
        self.mainToolBar.addWidget(speed_widget)
        self.speedSlider.valueChanged.connect(self._on_speed_changed)

    def _on_speed_changed(self, value: int):
        delay_ms = int((value / 10) ** 2 * 2000)
        self.interpreter.set_execution_speed(delay_ms)
        labels = ["▶▶", "▶▶", "▶", "▶", "▷▷", "▷▷", "▷", "▷", "▷", "·▷", "··"]
        colors = [
            "#4ade80", "#4ade80", "#4ade80", "#86efac", "#fbbf24", "#fbbf24",
            "#f59e0b", "#f59e0b", "#ef4444", "#ef4444", "#ef4444",
        ]
        self.speedLabel.setText(labels[value])
        self.speedLabel.setStyleSheet(
            f"color: {colors[value]}; font-size: 10px; min-width: 24px;"
        )

    def _setup_file_menu(self):
        examples_menu = self.menuFile.addMenu("📚  Örnekler")
        from collections import defaultdict
        by_category = defaultdict(list)
        for name, tpl in TEMPLATES.items():
            by_category[tpl["category"]].append(name)
        for category, names in by_category.items():
            cat_action = QAction(f"── {category} ──", self)
            cat_action.setEnabled(False)
            examples_menu.addAction(cat_action)
            for name in names:
                action = QAction(f"  {name}", self)
                action.setToolTip(TEMPLATES[name]["description"])
                action.triggered.connect(
                    lambda checked=False, n=name: self._load_template(n)
                )
                examples_menu.addAction(action)
            examples_menu.addSeparator()
        self.menuFile.addSeparator()

        save_action = QAction("💾  Save…", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_flow)
        self.menuFile.addAction(save_action)

        load_action = QAction("📂  Open…", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self._load_flow)
        self.menuFile.addAction(load_action)

        export_img_action = QAction("🖼  Flow Görüntüsü Dışa Aktar…", self)
        export_img_action.setShortcut("Ctrl+Shift+E")
        export_img_action.triggered.connect(self._export_flow_image)
        self.menuFile.addAction(export_img_action)

        pdf_action = QAction("📄  PDF Rapor Dışa Aktar…", self)
        pdf_action.setShortcut("Ctrl+Shift+P")
        pdf_action.triggered.connect(self._export_pdf_report)
        self.menuFile.addAction(pdf_action)

        self.menuFile.addSeparator()
        share_action = QAction("🔗  Paylaşım Linki Oluştur…", self)
        share_action.setShortcut("Ctrl+Shift+L")
        share_action.triggered.connect(self._share_flow_link)
        self.menuFile.addAction(share_action)

        open_link_action = QAction("🔗  Linkten Aç…", self)
        open_link_action.triggered.connect(self._open_flow_from_link)
        self.menuFile.addAction(open_link_action)

    def _load_template(self, name: str):
        if self.registry.get_all_nodes():
            reply = QMessageBox.question(
                self, "Şablon Yükle",
                "Mevcut flow silinecek. Devam edilsin mi?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        if load_template(name, self.registry, self.current_scene):
            self._page_states[self._current_page_key] = FlowSerializer.serialize_to_dict(
                self.registry
            )
            self.undo_manager._undo_stack.clear()
            self.undo_manager._redo_stack.clear()
            self.undo_manager.save_snapshot()
            self._update_live_generation()
            self.statusbar.showMessage(f"✔ Şablon yüklendi: {name}", 3000)
            self._fit_to_flow()
        else:
            self.statusbar.showMessage(f"❌ Şablon yüklenemedi: {name}", 3000)

    def _setup_edit_menu(self):
        """Edit menüsünü çalışır undo/redo eylemleriyle doldurur."""
        self._undo_action = QAction("↩️  Undo", self)
        self._undo_action.setShortcut("Ctrl+Z")
        self._undo_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self._undo_action.triggered.connect(self._perform_undo)
        self.menuEdit.addAction(self._undo_action)
        self.addAction(self._undo_action)

        self._redo_action = QAction("↪️  Redo", self)
        self._redo_action.setShortcut("Ctrl+Y")
        self._redo_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self._redo_action.triggered.connect(self._perform_redo)
        self.menuEdit.addAction(self._redo_action)
        self.addAction(self._redo_action)

        self.menuEdit.addSeparator()
        copy_action = QAction("📋  Kopyala", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        copy_action.triggered.connect(self.current_scene.copy_selected)
        self.menuEdit.addAction(copy_action)

        paste_action = QAction("📌  Yapıştır", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        paste_action.triggered.connect(self.current_scene.paste_nodes)
        self.menuEdit.addAction(paste_action)

        duplicate_action = QAction("⧉  Çoğalt", self)
        duplicate_action.setShortcut("Ctrl+D")
        duplicate_action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        duplicate_action.triggered.connect(self._duplicate_selection)
        self.menuEdit.addAction(duplicate_action)

        self.menuEdit.addSeparator()
        align_menu = self.menuEdit.addMenu("⬛  Hizala")
        for label, mode in [
            ("→ Yatay", "horizontal"),
            ("↓ Dikey", "vertical"),
            ("▦ Izgara", "grid"),
        ]:
            action = QAction(label, self)
            action.triggered.connect(
                lambda checked=False, m=mode: self.current_scene.auto_layout(m)
            )
            align_menu.addAction(action)

    def _duplicate_selection(self):
        self.current_scene.copy_selected()
        self.current_scene.paste_nodes()

    def eventFilter(self, obj, event):
        """Canvas odaktayken Ctrl+Z / Ctrl+Y kısayollarını yakalar."""
        if obj is self.graphicsView and event.type() == QEvent.Type.KeyPress:
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                if event.key() == Qt.Key.Key_Z:
                    self._perform_undo()
                    return True
                if event.key() == Qt.Key.Key_Y:
                    self._perform_redo()
                    return True
                if event.key() == Qt.Key.Key_C:
                    self.current_scene.copy_selected()
                    return True
                if event.key() == Qt.Key.Key_V:
                    self.current_scene.paste_nodes()
                    return True
                if event.key() == Qt.Key.Key_D:
                    self._duplicate_selection()
                    return True
        return super().eventFilter(obj, event)

    def _perform_undo(self):
        """Canvas geri alma + panelleri yenile."""
        if not self.undo_manager.undo():
            self.statusbar.showMessage("Geri alınacak işlem yok.", 2000)
            return
        self._after_history_restore()
        self.statusbar.showMessage("↩ Geri alındı.", 1500)

    def _perform_redo(self):
        """Canvas ileri alma + panelleri yenile."""
        if not self.undo_manager.redo():
            self.statusbar.showMessage("İleri alınacak işlem yok.", 2000)
            return
        self._after_history_restore()
        self.statusbar.showMessage("↪ İleri alındı.", 1500)

    def _after_history_restore(self):
        """Undo/redo sonrası sahne durumunu panellerle senkronize eder."""
        self._page_states[self._current_page_key] = FlowSerializer.serialize_to_dict(
            self.registry
        )
        self._clear_all_highlights()
        self._update_properties_panel()
        self._update_style_panel()
        self._update_live_generation()

    def _setup_view_menu(self):
        """View menüsünü görünüm eylemleriyle doldurur."""
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(self._zoom_in)
        self.menuView.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self._zoom_out)
        self.menuView.addAction(zoom_out_action)

        reset_zoom_action = QAction("Reset Zoom", self)
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.triggered.connect(self._reset_zoom)
        self.menuView.addAction(reset_zoom_action)

        fit_action = QAction("Fit to Flow", self)
        fit_action.setShortcut("Ctrl+9")
        fit_action.triggered.connect(self._fit_to_flow)
        self.menuView.addAction(fit_action)

        self.menuView.addSeparator()
        self.menuView.addAction(self.nodePanelDock.toggleViewAction())
        self.menuView.addAction(self.rightPanelDock.toggleViewAction())
        self.menuView.addAction(self.consoleDock.toggleViewAction())

        self.menuView.addSeparator()
        settings_action = QAction(t("settings"), self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._open_settings)
        self.menuView.addAction(settings_action)

        restart_tour_action = QAction(t("restart_tour"), self)
        restart_tour_action.triggered.connect(self._restart_guided_tour)
        self.menuView.addAction(restart_tour_action)

        minimap_action = QAction("🗺  Minimap", self)
        minimap_action.setCheckable(True)
        minimap_action.setChecked(True)
        minimap_action.toggled.connect(
            lambda v: self._minimap.setVisible(v) if hasattr(self, "_minimap") else None
        )
        self.menuView.addAction(minimap_action)

        self.menuFile.addSeparator()
        self.menuFile.addAction(self._undo_action)
        self.menuFile.addAction(self._redo_action)

    def _save_flow(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Flow", "", "FlowPy File (*.flowpy);;JSON (*.json)"
        )
        if filepath:
            nodes_count, edges_count = FlowSerializer.save_to_file(
                filepath, self.registry, self.current_scene
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
                filepath, self.registry, self.current_scene
            )
            self.statusbar.showMessage(
                f"✔ Loaded: {nodes_count} nodes, {edges_count} edges ← {filepath}"
            )

    # ── Vurgulama ─────────────────────────────────────────────────────

    def _highlight_node(self, node):
        for item in self.current_scene.items():
            if isinstance(item, BaseNode) and item is not node:
                if hasattr(item, "set_highlight"):
                    item.set_highlight(False)
        if hasattr(node, "set_highlight"):
            node.set_highlight(True)
        else:
            node._highlight_active = True
            node.update()

    def _highlight_edge(self, edge):
        edge.set_animating(True)
        self._active_edges.append(edge)

    def _clear_all_highlights(self):
        for item in self.current_scene.items():
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
            selected = self.current_scene.selectedItems()
        except RuntimeError:
            return

        nodes = [item for item in selected if isinstance(item, BaseNode)]

        if not nodes:
            self.propNodeTitle.setText(t("no_node_selected"))
            self.propNodeId.setText("")
            self.propDetails.clear()
            if hasattr(self, "propNodeBadge"):
                self.propNodeBadge.setStyleSheet("")
            self.propNodeTitle.setStyleSheet("")
            self.propNodeId.setStyleSheet("")
            return

        node = nodes[0]
        short_id = node.node_id[:8] if len(node.node_id) >= 8 else node.node_id
        theme = BaseNode.NODE_THEME.get(node.title, BaseNode.DEFAULT_THEME)

        if hasattr(self, "propNodeBadge"):
            self.propNodeBadge.setStyleSheet(f"""
                QWidget#propNodeBadge {{
                    background: {theme['bg']};
                    border: 1px solid {theme['border']};
                    border-radius: 8px;
                    padding: 8px;
                }}
            """)
        self.propNodeTitle.setText(node.title)
        self.propNodeTitle.setStyleSheet(
            f"color: {theme['text']}; font-weight: bold; font-size: 13px;"
        )
        self.propNodeId.setText(f"ID: {short_id}…")
        self.propNodeId.setStyleSheet("color: #444444; font-size: 10px;")

        lines = []
        for key, value in node.properties.items():
            display_value = value if value else "(unset)"
            lines.append(f"<b>{key}:</b><br>{display_value}")

        lines.append(f"<br><b>Input Ports:</b> {len(node.input_ports)}")
        lines.append(f"<b>Output Ports:</b> {len(node.output_ports)}")
        lines.append(f"<b>Connections:</b> {len(node.edges)}")

        if node.title == "Decision":
            lines.append("""
<div style='margin-top:8px;display:flex;gap:6px'>
  <span style='background:#14291a;color:#4ade80;font-size:10px;
               padding:2px 8px;border-radius:4px;font-weight:600'>Port 0 → True</span>
  <span style='background:#1e1200;color:#fbbf24;font-size:10px;
               padding:2px 8px;border-radius:4px;font-weight:600'>Port 1 → False</span>
</div>
""")

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

    def _export_flow_image(self):
        from PyQt6.QtGui import QImage, QPainter
        from PyQt6.QtCore import QRectF

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Flow'u Dışa Aktar",
            "flow_diagram.png",
            "PNG Görüntü (*.png);;SVG Vektör (*.svg)",
        )
        if not filepath:
            return
        rect = self.current_scene.itemsBoundingRect()
        if rect.isNull():
            self.statusbar.showMessage("⚠ Dışa aktarılacak içerik yok.", 3000)
            return
        margin = 40
        rect = rect.adjusted(-margin, -margin, margin, margin)
        if filepath.lower().endswith(".svg"):
            from PyQt6.QtSvg import QSvgGenerator
            generator = QSvgGenerator()
            generator.setFileName(filepath)
            generator.setSize(rect.size().toSize())
            generator.setViewBox(rect)
            painter = QPainter(generator)
            self.current_scene.render(painter, QRectF(), rect)
            painter.end()
        else:
            scale = 2
            image = QImage(
                int(rect.width() * scale), int(rect.height() * scale),
                QImage.Format.Format_ARGB32,
            )
            image.fill(Qt.GlobalColor.transparent)
            painter = QPainter(image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.scale(scale, scale)
            self.current_scene.render(painter, QRectF(), rect)
            painter.end()
            image.save(filepath)
        self.statusbar.showMessage(f"✔ Dışa aktarıldı: {filepath}", 4000)

    def _export_pdf_report(self):
        import datetime
        import re
        from PyQt6.QtGui import QPainter, QPageSize, QFont, QColor
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtCore import QRectF, QMarginsF

        filepath, _ = QFileDialog.getSaveFileName(
            self, "PDF Rapor Dışa Aktar", "flowpy_report.pdf", "PDF (*.pdf)"
        )
        if not filepath:
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(filepath)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageMargins(QMarginsF(20, 20, 20, 20), QPrinter.Unit.Millimeter)

        painter = QPainter(printer)
        page_rect = QRectF(printer.pageRect(QPrinter.Unit.DevicePixel))
        y = 0
        line_h = 14

        painter.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        painter.setPen(QColor("#1e3a6e"))
        painter.drawText(QRectF(0, y, page_rect.width(), 50), Qt.AlignmentFlag.AlignLeft, "FlowPy")
        y += 55

        painter.setFont(QFont("Segoe UI", 11))
        painter.setPen(QColor("#666"))
        now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        node_count = len(self.registry.get_all_nodes())
        edge_count = len(self.registry.edges)
        painter.drawText(
            QRectF(0, y, page_rect.width(), 20), Qt.AlignmentFlag.AlignLeft,
            f"Oluşturulma: {now}  ·  {node_count} düğüm  ·  {edge_count} bağlantı",
        )
        y += 30
        painter.setPen(QColor("#ddd"))
        painter.drawLine(0, int(y), int(page_rect.width()), int(y))
        y += 20

        items_rect = self.current_scene.itemsBoundingRect()
        if not items_rect.isNull():
            avail_h = page_rect.height() * 0.45
            avail_w = page_rect.width()
            self.current_scene.render(painter, QRectF(0, y, avail_w, avail_h), items_rect)
            y += avail_h + 20

        printer.newPage()
        y = 0
        painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        painter.setPen(QColor("#1e3a6e"))
        painter.drawText(
            QRectF(0, y, page_rect.width(), 30), Qt.AlignmentFlag.AlignLeft, "Üretilen Python Kodu"
        )
        y += 40
        code = self.codeGenOutput.toPlainText()
        painter.setFont(QFont("Consolas", 9))
        painter.setPen(QColor("#1a1a1a"))
        painter.fillRect(QRectF(0, y, page_rect.width(), page_rect.height() - y - 20), QColor("#f8f8f8"))
        for line in code.split("\n"):
            if y + line_h > page_rect.height() - 20:
                printer.newPage()
                y = 20
            painter.drawText(QRectF(8, y, page_rect.width() - 16, line_h), Qt.AlignmentFlag.AlignLeft, line)
            y += line_h

        console_text = self.consoleOutput.toPlainText()
        if console_text.strip():
            printer.newPage()
            y = 0
            painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            painter.setPen(QColor("#1e3a6e"))
            painter.drawText(
                QRectF(0, y, page_rect.width(), 30), Qt.AlignmentFlag.AlignLeft, "Çalıştırma Logu"
            )
            y += 40
            painter.setFont(QFont("Consolas", 9))
            painter.setPen(QColor("#333"))
            for line in console_text.split("\n"):
                if y + line_h > page_rect.height() - 20:
                    printer.newPage()
                    y = 20
                clean = re.sub(r"<[^>]+>", "", line)
                painter.drawText(QRectF(0, y, page_rect.width(), line_h), Qt.AlignmentFlag.AlignLeft, clean)
                y += line_h

        painter.end()
        self.statusbar.showMessage(f"✔ PDF raporu oluşturuldu: {filepath}", 4000)

    def _share_flow_link(self):
        import json
        import base64
        import zlib

        flow_dict = FlowSerializer.serialize_to_dict(self.registry)
        json_bytes = json.dumps(flow_dict, ensure_ascii=False).encode("utf-8")
        compressed = zlib.compress(json_bytes, level=9)
        encoded = base64.urlsafe_b64encode(compressed).decode("ascii")
        share_url = f"flowpy://share#{encoded}"

        dialog = QDialog(self)
        dialog.setWindowTitle("Flow'u Paylaş")
        dialog.setFixedSize(480, 160)
        dialog.setStyleSheet("background: #1e1e1e; color: #ddd;")
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(QLabel("Bu linki kopyala ve arkadaşınla paylaş:"))
        url_field = QLineEdit(share_url)
        url_field.setReadOnly(True)
        url_field.selectAll()
        copy_btn = QPushButton("📋  Panoya Kopyala")

        def do_copy():
            QApplication.clipboard().setText(share_url)
            copy_btn.setText("✔  Kopyalandı!")

        copy_btn.clicked.connect(do_copy)
        layout.addWidget(url_field)
        layout.addWidget(copy_btn)
        node_count = len(self.registry.get_all_nodes())
        layout.addWidget(QLabel(f"{node_count} düğüm · {len(encoded) / 1024:.1f} KB link boyutu"))
        dialog.exec()

    def _open_flow_from_link(self):
        import json
        import base64
        import zlib

        url, ok = QInputDialog.getText(self, "Link ile Aç", "FlowPy paylaşım linkini yapıştır:")
        if not ok or not url.strip():
            return
        try:
            encoded = url.split("#", 1)[1] if "#" in url else url.strip()
            compressed = base64.urlsafe_b64decode(encoded.encode("ascii"))
            flow_dict = json.loads(zlib.decompress(compressed).decode("utf-8"))
            FlowSerializer.deserialize_from_dict(
                flow_dict, self.registry, self.current_scene
            )
            self._page_states[self._current_page_key] = FlowSerializer.serialize_to_dict(
                self.registry
            )
            self.undo_manager.save_snapshot()
            self._update_live_generation()
            self.statusbar.showMessage("✔ Flow linkten yüklendi.", 3000)
        except Exception as e:
            self.statusbar.showMessage(f"❌ Link geçersiz: {e}", 4000)

    def _update_toolbar_state(self, is_active: bool, is_paused: bool):
        if is_active and not self._was_flow_active:
            if hasattr(self, "sparkline_panel"):
                self.sparkline_panel.reset()
        self._was_flow_active = is_active

        if not is_active:
            self.actionRunFlow.setEnabled(True)
            self.actionStepFlow.setEnabled(True)
            self.actionStopFlow.setEnabled(False)
            self.actionRunFlow.setText(t("run_all"))
            self.variableTable.setRowCount(0)
            self.statusbar.setStyleSheet(
                "QStatusBar { background: #111111; color: #444444; "
                "border-top: 1px solid #1e1e1e; }"
            )
            self.statusbar.showMessage(t("ready_message"))
        else:
            if is_paused:
                self.actionRunFlow.setEnabled(True)
                self.actionStepFlow.setEnabled(True)
                self.actionStopFlow.setEnabled(True)
                self.actionRunFlow.setText(t("continue_run"))
                self.statusbar.setStyleSheet(
                    "QStatusBar { background: #1e1200; color: #fbbf24; "
                    "border-top: 1px solid #3d2800; }"
                )
                self.statusbar.showMessage(
                    f"⏸ Duraklatıldı  ·  Adım: {self.interpreter._current_step}"
                )
            else:
                self.actionRunFlow.setEnabled(False)
                self.actionStepFlow.setEnabled(False)
                self.actionStopFlow.setEnabled(True)
                self.statusbar.setStyleSheet(
                    "QStatusBar { background: #0d1a0d; color: #4ade80; "
                    "border-top: 1px solid #1a6b38; }"
                )
                node_count = len(self.registry.get_all_nodes())
                edge_count = len(self.registry.edges)
                self.statusbar.showMessage(
                    f"● Çalışıyor  ·  {node_count} node · {edge_count} edge"
                )

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

THEMES = {
    "dark": {
        "bg": "#1e1e1e", "panel": "#2a2a2a", "base": "#161616",
        "accent": "#4078c8", "highlight": "#376ec8", "text": "#dcdcdc",
        "border": "#333333", "input_bg": "#1a2030",
    },
    "light": {
        "bg": "#f0f0f0", "panel": "#ffffff", "base": "#ffffff",
        "accent": "#2a5cbf", "highlight": "#2a5cbf", "text": "#1a1a1a",
        "border": "#cccccc", "input_bg": "#ffffff",
    },
    "ocean": {
        "bg": "#0d1b2a", "panel": "#1a2d3f", "base": "#0a1520",
        "accent": "#00b4d8", "highlight": "#0096c7", "text": "#cce7f0",
        "border": "#1e3a50", "input_bg": "#122535",
    },
}


def _build_stylesheet(theme: dict) -> str:
    """Tema renklerinden global Qt stylesheet üretir."""
    bg = theme["bg"]
    panel = theme["panel"]
    base = theme["base"]
    accent = theme["accent"]
    highlight = theme["highlight"]
    text = theme["text"]
    border = theme["border"]
    input_bg = theme["input_bg"]
    return f"""
        QMainWindow, QWidget {{
            font-family: "Segoe UI", sans-serif;
            font-size: 11px;
        }}
        QMenuBar {{
            background-color: {bg};
            color: {text};
            border-bottom: 1px solid {border};
            padding: 2px 4px;
        }}
        QMenuBar::item:selected {{ background: {accent}; border-radius: 4px; }}
        QMenu {{
            background-color: {panel};
            color: {text};
            border: 1px solid {border};
        }}
        QMenu::item:selected {{ background: {accent}; }}
        QToolBar {{
            background-color: {panel};
            border-bottom: 1px solid {border};
            padding: 3px 6px;
            spacing: 6px;
        }}
        QToolBar QToolButton {{
            color: {text};
            background: {panel};
            border: 1px solid {border};
            border-radius: 5px;
            padding: 4px 10px;
            font-weight: bold;
        }}
        QToolBar QToolButton:hover {{ background: {accent}; border-color: {accent}; }}
        QToolBar QToolButton:pressed {{ background: {highlight}; }}
        QToolBar QToolButton:disabled {{ color: #888; }}
        QDockWidget::title {{
            background: {panel};
            border-bottom: 2px solid {accent};
            padding: 4px 8px;
            text-align: left;
        }}
        QTabWidget::pane {{ border: 1px solid {border}; background: {panel}; }}
        QTabBar::tab {{
            background: {bg};
            color: {text};
            border: 1px solid {border};
            padding: 5px 12px;
        }}
        QTabBar::tab:selected {{
            background: {panel};
            border-top: 2px solid {accent};
        }}
        QTreeWidget {{
            background-color: {bg};
            color: {text};
            border: none;
        }}
        QTreeWidget::item:hover {{ background: {accent}33; }}
        QTreeWidget::item:selected {{ background: {accent}; color: #fff; }}
        QLineEdit {{
            background: {input_bg};
            color: {text};
            border: 1px solid {border};
            border-radius: 6px;
            padding: 4px 8px;
        }}
        QLineEdit:focus {{ border-color: {accent}; }}
        QTableWidget {{
            background: {bg};
            color: {text};
            gridline-color: {border};
            border: none;
        }}
        QHeaderView::section {{
            background: {panel};
            color: {text};
            border: none;
            padding: 4px;
        }}
        QTextEdit, QTextBrowser {{
            background: {base};
            color: {text};
            border: 1px solid {border};
            border-radius: 4px;
        }}
        QScrollBar:vertical {{ background: {bg}; width: 8px; }}
        QScrollBar::handle:vertical {{ background: {border}; border-radius: 4px; }}
        QComboBox {{
            background: {panel};
            color: {text};
            border: 1px solid {border};
            border-radius: 4px;
            padding: 3px 8px;
        }}
        QComboBox QAbstractItemView {{
            background: {panel};
            selection-background-color: {accent};
        }}
        QSlider::handle:horizontal {{
            background: {accent};
            border-radius: 7px;
        }}
        QSlider::sub-page:horizontal {{ background: {accent}; }}
        #bottomBar {{
            background: {bg};
            border-top: 1px solid {border};
        }}
        QStatusBar {{
            background: {base};
            color: {text};
            border-top: 1px solid {border};
            font-size: 10px;
        }}
        QPushButton {{
            background: {panel};
            color: {text};
            border: 1px solid {border};
            border-radius: 4px;
            padding: 4px 10px;
        }}
        QPushButton:hover {{ border-color: {accent}; }}
    """


def setup_theme(theme_name: str, app: QApplication):
    """Seçilen temayı uygular — Fusion palette + global stylesheet."""
    theme = THEMES.get(theme_name, THEMES["dark"])
    app.setStyle("Fusion")
    palette = QPalette()

    bg = QColor(theme["bg"])
    panel = QColor(theme["panel"])
    text = QColor(theme["text"])
    accent = QColor(theme["accent"])
    highlight = QColor(theme["highlight"])

    palette.setColor(QPalette.ColorRole.Window, bg)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, QColor(theme["base"]))
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
    app.setStyleSheet(_build_stylesheet(theme))


def setup_dark_theme(app: QApplication):
    """Geriye dönük uyumluluk — koyu temayı uygular."""
    setup_theme("dark", app)


# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "FlowPy.ModernAlgorithmIDE"
            )
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(APP_ICON_PATH))
    SettingsManager.instance().ensure_defaults()
    theme_name = SettingsManager.instance().get("theme", "dark")
    setup_theme(theme_name, app)
    window = FlowPyApp()
    window.show()
    sys.exit(app.exec())