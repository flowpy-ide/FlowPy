# models/node.py
# ──────────────────────────────────────────────────────────────────────
# BaseNode  : QGraphicsItem tabanlı sürüklenebilir düğüm.
# Port      : Düğümlerin giriş/çıkış bağlantı noktaları.
# ──────────────────────────────────────────────────────────────────────

import math

from PyQt6.QtWidgets import QGraphicsItem, QGraphicsEllipseItem, QGraphicsDropShadowEffect
from PyQt6.QtCore import QRectF, Qt, QPointF, QTimer
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QRadialGradient, QPainterPath,
)

from core.node_visuals import build_shape_path, get_node_shape
from core.i18n_nodes import (
    tn, t_node, resolve_canonical_node_title, default_properties_for, NODE_PROPERTY_SCHEMA,
)


# ═══════════════════════════════════════════════════════════════════════
#  Port (Bağlantı Noktası)
# ═══════════════════════════════════════════════════════════════════════

class Port(QGraphicsEllipseItem):
    """Düğüm üzerindeki giriş veya çıkış bağlantı noktası."""

    RADIUS = 6

    def __init__(self, parent_node, is_output: bool = False, label: str = ""):
        diameter = self.RADIUS * 2
        super().__init__(-self.RADIUS, -self.RADIUS, diameter, diameter,
                         parent_node)
        self.is_output = is_output
        self.label = label
        self._apply_theme_style(parent_node, is_output)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setAcceptHoverEvents(True)

    def _apply_theme_style(self, parent_node, is_output: bool):
        cls = type(parent_node)
        theme = cls.NODE_THEME.get(
            getattr(parent_node, "title", ""), cls.DEFAULT_THEME
        )
        glow = QColor(theme["glow"])
        if is_output:
            fill = QColor(theme["bg"])
        else:
            fill = QColor("#141414")
        self._base_fill = fill
        self._base_pen = glow
        self.setBrush(QBrush(fill))
        self.setPen(QPen(glow, 2))

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor("#f1c40f")))
        self.setScale(1.4)
        parent = self.parentItem()
        if isinstance(parent, BaseNode):
            parent._show_doc_tooltip()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(self._base_fill))
        self.setPen(QPen(self._base_pen, 2))
        self.setScale(1.0)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            scene = self.scene()
            if scene and hasattr(scene, 'start_connection'):
                scene.start_connection(self)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        scene = self.scene()
        if scene and hasattr(scene, 'update_connection'):
            scene.update_connection(event.scenePos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            scene = self.scene()
            if scene and hasattr(scene, 'finish_connection'):
                scene.finish_connection(event.scenePos())
                event.accept()
                return
        super().mouseReleaseEvent(event)


# ═══════════════════════════════════════════════════════════════════════
#  BaseNode (Temel Düğüm)
# ═══════════════════════════════════════════════════════════════════════

class BaseNode(QGraphicsItem):
    """Sahneye yerleştirilebilen, sürüklenebilir temel düğüm."""

    WIDTH = 160
    HEIGHT = 80
    CORNER_RADIUS = 10

    NODE_THEME = {
        "Start":    {"bg": "#0d2e1a", "border": "#1a6b38", "text": "#4ade80", "glow": "#22c55e"},
        "Process":  {"bg": "#0d1e3a", "border": "#1a3d6e", "text": "#60a5fa", "glow": "#3b82f6"},
        "Decision": {"bg": "#1e1200", "border": "#3d2800", "text": "#fbbf24", "glow": "#f59e0b"},
        "Input":    {"bg": "#0d2e1a", "border": "#1a6b38", "text": "#4ade80", "glow": "#22c55e"},
        "Output":   {"bg": "#0d2e1a", "border": "#1a6b38", "text": "#4ade80", "glow": "#22c55e"},
        "While":    {"bg": "#1a0d2e", "border": "#3a1a6e", "text": "#a78bfa", "glow": "#8b5cf6"},
        "For":      {"bg": "#1a0d2e", "border": "#3a1a6e", "text": "#a78bfa", "glow": "#8b5cf6"},
        "Function": {"bg": "#2e0d1e", "border": "#6e1a3a", "text": "#f472b6", "glow": "#ec4899"},
        "Return":   {"bg": "#2e0d1e", "border": "#6e1a3a", "text": "#f472b6", "glow": "#ec4899"},
        "Variable":          {"bg": "#0d1e3a", "border": "#1a3d6e", "text": "#60a5fa", "glow": "#3b82f6"},
        "Print":             {"bg": "#0d2e1a", "border": "#1a6b38", "text": "#4ade80", "glow": "#22c55e"},
        "Math":              {"bg": "#0d1e3a", "border": "#1a3d6e", "text": "#60a5fa", "glow": "#3b82f6"},
        "String Operation":  {"bg": "#0d1e3a", "border": "#1a3d6e", "text": "#60a5fa", "glow": "#3b82f6"},
        "Type Cast":         {"bg": "#0d1e3a", "border": "#1a3d6e", "text": "#60a5fa", "glow": "#3b82f6"},
        "List Operation":    {"bg": "#0d1e3a", "border": "#1a3d6e", "text": "#60a5fa", "glow": "#3b82f6"},
        "If Elif Else":      {"bg": "#1e1200", "border": "#3d2800", "text": "#fbbf24", "glow": "#f59e0b"},
        "Break":             {"bg": "#2e0d0d", "border": "#6e1a1a", "text": "#fca5a5", "glow": "#ef4444"},
        "Continue":          {"bg": "#0d1a2e", "border": "#1a3a6e", "text": "#93c5fd", "glow": "#3b82f6"},
        "Try Except":        {"bg": "#2e1200", "border": "#6e2800", "text": "#fb923c", "glow": "#f97316"},
        "Switch Match":      {"bg": "#1e1200", "border": "#3d2800", "text": "#fbbf24", "glow": "#f59e0b"},
        "Stop":              {"bg": "#2e0d0d", "border": "#6e1a1a", "text": "#f87171", "glow": "#ef4444"},
        "Comment":           {"bg": "#1a1a1a", "border": "#3a3a3a", "text": "#888888", "glow": "#555555"},
        "Group":             {"bg": "#111111", "border": "#2a2a2a", "text": "#666666", "glow": "#444444"},
        "Delay":             {"bg": "#1a0d2e", "border": "#3a1a6e", "text": "#a78bfa", "glow": "#8b5cf6"},
        "File Read":         {"bg": "#0d2e1a", "border": "#1a6b38", "text": "#4ade80", "glow": "#22c55e"},
        "File Write":        {"bg": "#0d2e1a", "border": "#1a6b38", "text": "#4ade80", "glow": "#22c55e"},
        "Random":            {"bg": "#1e1200", "border": "#3d2800", "text": "#fbbf24", "glow": "#f59e0b"},
        "Sort":              {"bg": "#2e0d1e", "border": "#6e1a3a", "text": "#f472b6", "glow": "#ec4899"},
        "Search":            {"bg": "#2e0d1e", "border": "#6e1a3a", "text": "#f472b6", "glow": "#ec4899"},
        "Swap":              {"bg": "#2e0d1e", "border": "#6e1a3a", "text": "#f472b6", "glow": "#ec4899"},
        "Accumulate":        {"bg": "#2e0d1e", "border": "#6e1a3a", "text": "#f472b6", "glow": "#ec4899"},
        "Lambda":            {"bg": "#0d1a2e", "border": "#1a3a5e", "text": "#38bdf8", "glow": "#0ea5e9"},
        "List Comprehension":{"bg": "#0d1a2e", "border": "#1a3a5e", "text": "#38bdf8", "glow": "#0ea5e9"},
        "Assert":            {"bg": "#0d1a2e", "border": "#1a3a5e", "text": "#38bdf8", "glow": "#0ea5e9"},
        "Import":            {"bg": "#0d1a2e", "border": "#1a3a5e", "text": "#38bdf8", "glow": "#0ea5e9"},
    }
    DEFAULT_THEME = {
        "bg": "#1e1e1e", "border": "#3a3a3a", "text": "#dcdcdc", "glow": "#4078c8",
    }

    def __init__(self, title: str = "Process", node_id: str = ""):
        super().__init__()
        self.title = resolve_canonical_node_title(title)
        self.node_id = node_id

        self.properties: dict = default_properties_for(self.title)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self._hover = False
        self._has_breakpoint = False

        self.input_ports: list[Port] = []
        self.output_ports: list[Port] = []
        self._create_ports()
        self.edges: list = []

        self._highlight_active = False
        self._pulse_opacity = 1.0
        self._pulse_timer = QTimer()
        self._pulse_timer.timeout.connect(self._pulse_tick)
        self._pulse_phase = 0

        self._custom_color: str | None = None
        self._custom_border_style: int = 0
        self._border_pen_style = None
        self._custom_line_style: int = 0
        self._line_pen_style = None

        self.glow_effect = QGraphicsDropShadowEffect()
        self.glow_effect.setBlurRadius(25)
        self.glow_effect.setColor(QColor("#f39c12"))
        self.glow_effect.setOffset(0, 0)
        self.glow_effect.setEnabled(False)
        self.setGraphicsEffect(self.glow_effect)

        self._refresh_cached_colors()

    def normalize_title_and_properties(self):
        """Eski TR görünen adlar veya eksik özellikler için düğümü kanonik hale getirir."""
        fixed = resolve_canonical_node_title(self.title)
        if fixed != self.title:
            self.title = fixed
        merged = default_properties_for(self.title)
        for key, val in merged.items():
            self.properties.setdefault(key, val)
        if self.title == "Switch Match":
            self.rebuild_ports()
        self._refresh_cached_colors()
        self.update()

    def _refresh_cached_colors(self):
        """Tema renklerini önbelleğe alır (_custom_color öncelikli)."""
        theme = self.NODE_THEME.get(self.title, self.DEFAULT_THEME)
        if self._custom_color:
            self._color_bg = QColor(self._custom_color)
            self._color_border = self._color_bg.darker(130)
            self._color_text = QColor("#ffffff")
            self._color_glow = QColor(theme["glow"])
        else:
            self._color_bg = QColor(theme["bg"])
            self._color_border = QColor(theme["border"])
            self._color_text = QColor(theme["text"])
            self._color_glow = QColor(theme["glow"])
        self._color_text_dim = QColor(self._color_text)
        self._color_text_dim.setAlpha(int(255 * 0.6))

    def toggle_breakpoint(self):
        self._has_breakpoint = not self._has_breakpoint
        self.update()

    def _show_doc_tooltip(self):
        scene = self.scene()
        if not scene or not scene.views():
            return
        view = scene.views()[0]
        main = view.window()
        if hasattr(main, "_node_tooltip"):
            anchor = self.scenePos() + QPointF(self.WIDTH / 2, 0)
            local_pt = view.mapFromScene(anchor)
            gp = view.mapToGlobal(local_pt)
            main._node_tooltip.show_for_node(self.title, gp, placement="above")

    def hoverEnterEvent(self, event):
        super().hoverEnterEvent(event)
        self._hover = True
        self.update()
        self._show_doc_tooltip()

    def hoverLeaveEvent(self, event):
        super().hoverLeaveEvent(event)
        self._hover = False
        self.update()
        scene = self.scene()
        if scene and scene.views():
            main = scene.views()[0].window()
            if hasattr(main, "_node_tooltip"):
                main._node_tooltip.schedule_hide(500)

    def set_highlight(self, active: bool):
        self._highlight_active = active
        self.glow_effect.setEnabled(False)
        if active:
            self._pulse_phase = 0
            self._pulse_timer.start(50)
        else:
            self._pulse_timer.stop()
            self._pulse_opacity = 1.0
        self.update()

    def _pulse_tick(self):
        self._pulse_phase += 0.15
        self._pulse_opacity = 0.6 + 0.4 * abs(math.sin(self._pulse_phase))
        self.update()

    def _get_port_counts(self) -> tuple[int, int]:
        counts = {
            "Start": (0, 1), "Stop": (1, 0), "Break": (1, 0),
            "Return": (1, 1),  # çıkış: akış diyagramında devam bağlantısı
            "Comment": (0, 0), "Group": (0, 0),
            "Decision": (1, 2), "If Elif Else": (1, 3), "While": (1, 2), "For": (1, 2),
            "Try Except": (1, 2), "Search": (1, 2), "Assert": (1, 2),
        }
        if self.title == "Switch Match":
            cases = [c.strip() for c in self.properties.get("cases", "1,2,default").split(",") if c.strip()]
            return (1, max(len(cases), 1))
        return counts.get(self.title, (1, 1))

    def rebuild_ports(self):
        for port in self.input_ports + self.output_ports:
            port.setParentItem(None)
        self.input_ports.clear()
        self.output_ports.clear()
        self._create_ports()

    def _output_port_labels(self, out_count: int) -> list[str]:
        if self.title == "Decision":
            return ["True", "False"][:out_count]
        if self.title == "If Elif Else":
            return ["if", "elif", "else"][:out_count]
        if self.title in ("While", "For"):
            return ["Loop", "Exit"][:out_count]
        if self.title == "Try Except":
            return ["try", "except"][:out_count]
        if self.title == "Search":
            return ["found", "not found"][:out_count]
        if self.title == "Assert":
            return ["pass", "fail"][:out_count]
        if self.title == "Switch Match":
            cases = [c.strip() for c in self.properties.get("cases", "").split(",") if c.strip()]
            return cases[:out_count] if cases else [str(i) for i in range(out_count)]
        return [""] * out_count

    def _create_ports(self):
        in_count, out_count = self._get_port_counts()
        shape = get_node_shape(self.title)

        if in_count > 0:
            inp = Port(self, is_output=False)
            if shape == "diamond":
                inp.setPos(0, self.HEIGHT / 2)
            else:
                inp.setPos(0, self.HEIGHT / 2)
            self.input_ports.append(inp)

        if out_count == 0:
            return

        labels = self._output_port_labels(out_count)
        if out_count == 1:
            out = Port(self, is_output=True, label=labels[0])
            out.setPos(self.WIDTH, self.HEIGHT / 2)
            self.output_ports.append(out)
        else:
            for i in range(out_count):
                y_frac = (i + 1) / (out_count + 1)
                out = Port(self, is_output=True, label=labels[i])
                out.setPos(self.WIDTH, self.HEIGHT * y_frac)
                self.output_ports.append(out)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.WIDTH, self.HEIGHT)

    def update(self, *args):
        self._refresh_cached_colors()
        super().update(*args)

    def _body_path(self) -> QPainterPath:
        return build_shape_path(
            get_node_shape(self.title), self.boundingRect(), self.CORNER_RADIUS
        )

    def _draw_body(self, painter: QPainter, rect: QRectF):
        path = self._body_path()
        shape = get_node_shape(self.title)

        if self._highlight_active:
            glow = QColor(self._color_glow)
            glow.setAlphaF(self._pulse_opacity)
            painter.setPen(QPen(glow, 2.5))
            radial = QRadialGradient(
                rect.center().x(), rect.center().y(),
                max(rect.width(), rect.height()) * 0.75,
            )
            glow_fill = QColor(self._color_glow)
            glow_fill.setAlpha(18)
            radial.setColorAt(0, QColor(0, 0, 0, 0))
            radial.setColorAt(1, glow_fill)
            painter.setBrush(QBrush(radial))
            painter.drawPath(path)
            painter.setBrush(QBrush(self._color_bg))
            painter.setPen(QPen(glow, 2.5))
        elif self.isSelected():
            sel = QColor(self._color_glow)
            sel.setAlpha(200)
            painter.setPen(QPen(sel, 2.5))
            painter.setBrush(QBrush(self._color_bg))
        else:
            border_style = (
                self._border_pen_style
                if self._border_pen_style is not None
                else Qt.PenStyle.SolidLine
            )
            if border_style == Qt.PenStyle.NoPen:
                painter.setPen(Qt.PenStyle.NoPen)
            else:
                painter.setPen(QPen(self._color_border, 1.5, border_style))
            painter.setBrush(QBrush(self._color_bg))

        if shape == "note" and self.title in ("Comment", "Group"):
            painter.setPen(QPen(self._color_border, 1.2, Qt.PenStyle.DashLine))

        painter.drawPath(path)

    def _text_layout_rects(self) -> tuple[QRectF, QRectF]:
        """Şekle göre başlık ve alt satır alanları (ortalanmış metin)."""
        m = 10.0
        w = self.WIDTH - 2 * m
        shape = get_node_shape(self.title)
        if shape == "diamond":
            return (
                QRectF(m, 20, w, 30),
                QRectF(m, 50, w, 24),
            )
        if shape == "loop":
            return (
                QRectF(m, 16, w, 28),
                QRectF(m, 44, w, 28),
            )
        if shape in ("terminal", "terminal_stop"):
            return (
                QRectF(m, 14, w, 28),
                QRectF(m, 42, w, 26),
            )
        return (
            QRectF(m, 8, w, 32),
            QRectF(m, 42, w, 30),
        )

    def paint(self, painter: QPainter, option, widget=None):
        rect = self.boundingRect()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_body(painter, rect)

        if self._has_breakpoint:
            painter.setBrush(QBrush(QColor("#ef4444")))
            painter.setPen(QPen(QColor("#7f1d1d"), 1))
            painter.drawEllipse(QRectF(4, 4, 10, 10))

        title_rect, summary_rect = self._text_layout_rects()
        display_title = t_node(self.title)
        title_pt = 8 if len(display_title) > 18 else (9 if len(display_title) > 14 else 10)
        title_font = QFont("Segoe UI", title_pt, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QPen(self._color_text))
        align = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        metrics = painter.fontMetrics()
        elided_title = metrics.elidedText(
            display_title, Qt.TextElideMode.ElideRight, int(title_rect.width())
        )
        painter.drawText(title_rect, align, elided_title)

        summary = self._get_property_summary()
        if summary:
            small_font = QFont("Segoe UI", 7)
            painter.setFont(small_font)
            painter.setPen(QPen(self._color_text_dim))
            sm = painter.fontMetrics()
            elided = sm.elidedText(
                summary, Qt.TextElideMode.ElideRight, int(summary_rect.width())
            )
            painter.drawText(summary_rect, align, elided)

        if get_node_shape(self.title) == "diamond":
            label_font = QFont("Segoe UI", 7, QFont.Weight.Bold)
            painter.setFont(label_font)
            for i, port in enumerate(self.output_ports):
                y_frac = port.pos().y() / self.HEIGHT
                painter.setPen(QPen(QColor("#4ade80" if i == 0 else "#f59e0b")))
                label = (port.label[:5] if port.label else str(i))
                painter.drawText(
                    QRectF(self.WIDTH - 34, y_frac * self.HEIGHT - 10, 30, 12),
                    Qt.AlignmentFlag.AlignRight,
                    label,
                )
        elif self.title in ("While", "For"):
            label_font = QFont("Segoe UI", 7, QFont.Weight.Bold)
            painter.setFont(label_font)
            for i, port in enumerate(self.output_ports):
                y_frac = port.pos().y() / self.HEIGHT
                painter.setPen(QPen(QColor("#a78bfa" if i == 0 else "#8b5cf6")))
                label = "loop" if i == 0 else "out"
                painter.drawText(
                    QRectF(self.WIDTH - 34, y_frac * self.HEIGHT - 10, 30, 12),
                    Qt.AlignmentFlag.AlignRight,
                    label,
                )

    def _get_property_summary(self) -> str:
        hint = tn("hint_double_click")
        if self.title == "Decision":
            cond = self.properties.get("condition", "")
            return f"if {cond}" if cond else hint
        if self.title == "While":
            cond = self.properties.get("condition", "")
            return f"while {cond}" if cond else hint
        if self.title == "If Elif Else":
            c = self.properties.get("condition_if", "")
            return f"if {c}" if c else hint
        if self.title == "Process":
            code = self.properties.get("code", "")
            if code:
                return code.strip().split("\n")[0]
            return hint
        if self.title == "Start":
            vars_text = self.properties.get("variables", "")
            if vars_text:
                count = len([l for l in vars_text.strip().split("\n") if l.strip()])
                return tn("hint_var_count", n=count)
            return tn("hint_start")
        if self.title == "Variable":
            n = self.properties.get("name", "")
            return f"{n} = {self.properties.get('value', '')}" if n else hint
        if self.title in ("Break", "Continue"):
            tag = self.properties.get("tag", "").strip()
            desc = self.properties.get("description", "").strip()
            if tag:
                return tag
            if desc:
                return desc
            return hint
        schema = NODE_PROPERTY_SCHEMA.get(self.title, [])
        if schema:
            parts = []
            for prop_key, _, default in schema[:2]:
                val = self.properties.get(prop_key, default)
                if val:
                    parts.append(f"{prop_key}={val}")
            if parts:
                return " · ".join(parts)[:48]
            return hint
        return ""

    def mouseDoubleClickEvent(self, event):
        from views.node_editor_dialog import NodeEditorDialog

        self.normalize_title_and_properties()
        dialog = NodeEditorDialog(self)
        if dialog.exec():
            new_props = dialog.get_properties()
            self.properties.update(new_props)
            if self.title == "Switch Match":
                self.rebuild_ports()
            self.update()
            if self.scene() and hasattr(self.scene(), "history_changed"):
                self.scene().history_changed.emit()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.scene() and hasattr(self.scene(), "history_changed"):
            self.scene().history_changed.emit()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            grid_size = 20
            new_pos = value
            x = round(new_pos.x() / grid_size) * grid_size
            y = round(new_pos.y() / grid_size) * grid_size
            snapped_pos = QPointF(x, y)
            for edge in self.edges:
                edge.update_path()
            return snapped_pos
        return super().itemChange(change, value)
