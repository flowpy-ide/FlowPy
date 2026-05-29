# models/node.py
# ──────────────────────────────────────────────────────────────────────
# BaseNode  : QGraphicsItem tabanlı sürüklenebilir düğüm.
# Port      : Düğümlerin giriş/çıkış bağlantı noktaları.
# ──────────────────────────────────────────────────────────────────────

import math

from PyQt6.QtWidgets import QGraphicsItem, QGraphicsEllipseItem, QGraphicsDropShadowEffect
from PyQt6.QtCore import QRectF, Qt, QPointF, QTimer
from PyQt6.QtGui import (QPainter, QColor, QPen, QBrush, QFont, QRadialGradient)


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

_DEFAULT_PROPERTIES = {
    "Start":    {"variables": ""},
    "Process":  {"code": "", "description": ""},
    "Decision": {"condition": "", "description": ""},
    "While":    {"condition": "", "description": ""},
    "Input":    {"variable": "USER_IN", "prompt": "Değer girin:", "input_type": "auto"},
    "Output":   {"expression": ""},
    "For":      {"variable": "i", "start": "0", "end": "10", "step": "1"},
    "Function": {"function_name": "my_func", "parameters": ""},
    "Return":   {"expression": ""},
}


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
    }
    DEFAULT_THEME = {
        "bg": "#1e1e1e", "border": "#3a3a3a", "text": "#dcdcdc", "glow": "#4078c8",
    }

    def __init__(self, title: str = "Process", node_id: str = ""):
        super().__init__()
        self.title = title
        self.node_id = node_id

        defaults = _DEFAULT_PROPERTIES.get(title, {})
        self.properties: dict = dict(defaults)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

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

    def _create_ports(self):
        if self.title == "Decision":
            inp = Port(self, is_output=False)
            inp.setPos(0, self.HEIGHT / 2)
            self.input_ports.append(inp)

            out_true = Port(self, is_output=True, label="True")
            out_true.setPos(self.WIDTH, self.HEIGHT * 0.3)
            self.output_ports.append(out_true)

            out_false = Port(self, is_output=True, label="False")
            out_false.setPos(self.WIDTH, self.HEIGHT * 0.7)
            self.output_ports.append(out_false)

        elif self.title in ("While", "For"):
            inp = Port(self, is_output=False)
            inp.setPos(0, self.HEIGHT / 2)
            self.input_ports.append(inp)

            out_loop = Port(self, is_output=True, label="Loop")
            out_loop.setPos(self.WIDTH, self.HEIGHT * 0.3)
            self.output_ports.append(out_loop)

            out_exit = Port(self, is_output=True, label="Exit")
            out_exit.setPos(self.WIDTH, self.HEIGHT * 0.7)
            self.output_ports.append(out_exit)

        elif self.title == "Start":
            out = Port(self, is_output=True)
            out.setPos(self.WIDTH, self.HEIGHT / 2)
            self.output_ports.append(out)

        else:
            inp = Port(self, is_output=False)
            inp.setPos(0, self.HEIGHT / 2)
            self.input_ports.append(inp)

            out = Port(self, is_output=True)
            out.setPos(self.WIDTH, self.HEIGHT / 2)
            self.output_ports.append(out)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.WIDTH, self.HEIGHT)

    def update(self, *args):
        self._refresh_cached_colors()
        super().update(*args)

    def paint(self, painter: QPainter, option, widget=None):
        rect = self.boundingRect()
        painter.setBrush(QBrush(self._color_bg))

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
            painter.drawRoundedRect(rect, self.CORNER_RADIUS, self.CORNER_RADIUS)
            painter.setBrush(QBrush(self._color_bg))
            painter.setPen(QPen(glow, 2.5))
        elif self.isSelected():
            sel = QColor(self._color_glow)
            sel.setAlpha(200)
            painter.setPen(QPen(sel, 2.5))
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

        painter.drawRoundedRect(rect, self.CORNER_RADIUS, self.CORNER_RADIUS)

        title_rect = QRectF(0, 4, self.WIDTH, self.HEIGHT / 2)
        font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(self._color_text))
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self.title)

        summary = self._get_property_summary()
        if summary:
            summary_rect = QRectF(8, self.HEIGHT / 2 - 2, self.WIDTH - 16, self.HEIGHT / 2)
            small_font = QFont("Segoe UI", 7)
            painter.setFont(small_font)
            painter.setPen(QPen(self._color_text_dim))
            metrics = painter.fontMetrics()
            elided = metrics.elidedText(
                summary, Qt.TextElideMode.ElideRight, int(summary_rect.width())
            )
            painter.drawText(summary_rect, Qt.AlignmentFlag.AlignCenter, elided)

        if self.title == "Decision":
            label_font = QFont("Segoe UI", 7, QFont.Weight.Bold)
            painter.setFont(label_font)
            painter.setPen(QPen(QColor("#4ade80")))
            painter.drawText(
                QRectF(self.WIDTH - 30, self.HEIGHT * 0.3 - 10, 25, 12),
                Qt.AlignmentFlag.AlignRight, "✓",
            )
            painter.setPen(QPen(QColor("#f59e0b")))
            painter.drawText(
                QRectF(self.WIDTH - 30, self.HEIGHT * 0.7 - 2, 25, 12),
                Qt.AlignmentFlag.AlignRight, "✗",
            )
        elif self.title == "While":
            label_font = QFont("Segoe UI", 7, QFont.Weight.Bold)
            painter.setFont(label_font)
            painter.setPen(QPen(QColor("#a78bfa")))
            painter.drawText(
                QRectF(self.WIDTH - 30, self.HEIGHT * 0.3 - 10, 25, 12),
                Qt.AlignmentFlag.AlignRight, "🔁",
            )
            painter.setPen(QPen(QColor("#8b5cf6")))
            painter.drawText(
                QRectF(self.WIDTH - 30, self.HEIGHT * 0.7 - 2, 25, 12),
                Qt.AlignmentFlag.AlignRight, "➡",
            )

    def _get_property_summary(self) -> str:
        if self.title == "Decision":
            cond = self.properties.get("condition", "")
            return f"if {cond}" if cond else "⚙ Çift tıkla…"
        elif self.title == "While":
            cond = self.properties.get("condition", "")
            return f"while {cond}" if cond else "⚙ Çift tıkla…"
        elif self.title == "Process":
            code = self.properties.get("code", "")
            if code:
                return code.strip().split("\n")[0]
            return "⚙ Çift tıkla…"
        elif self.title == "Start":
            vars_text = self.properties.get("variables", "")
            if vars_text:
                count = len([l for l in vars_text.strip().split("\n") if l.strip()])
                return f"{count} değişken"
            return "▶ Başlangıç"
        return ""

    def mouseDoubleClickEvent(self, event):
        from views.node_editor_dialog import NodeEditorDialog

        dialog = NodeEditorDialog(self)
        if dialog.exec():
            new_props = dialog.get_properties()
            self.properties.update(new_props)
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
