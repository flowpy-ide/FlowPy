# views/minimap.py
# ──────────────────────────────────────────────────────────────────────
# FlowMinimap : Canvas köşesinde küçük navigasyon haritası.
# ──────────────────────────────────────────────────────────────────────

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush

from models.node import BaseNode


class FlowMinimap(QWidget):
    """Tüm sahneyi küçük ölçekte gösteren navigasyon haritası."""

    WIDTH = 160
    HEIGHT = 100
    PADDING = 8

    def __init__(self, view, scene, parent=None):
        super().__init__(parent)
        self.view = view
        self.scene = scene
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setStyleSheet("background: #111; border: 1px solid #2a2a2a; border-radius: 6px;")
        self.setCursor(Qt.CursorShape.CrossCursor)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(200)
        self._refresh_timer.timeout.connect(self.update)
        self._refresh_timer.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#111"))

        items_rect = self.scene.itemsBoundingRect()
        if items_rect.isNull() or items_rect.isEmpty():
            painter.setPen(QColor("#2a2a2a"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Boş")
            painter.end()
            return

        pad = self.PADDING
        avail_w = self.WIDTH - pad * 2
        avail_h = self.HEIGHT - pad * 2
        scale_x = avail_w / max(items_rect.width(), 1)
        scale_y = avail_h / max(items_rect.height(), 1)
        scale = min(scale_x, scale_y) * 0.9
        offset_x = pad + (avail_w - items_rect.width() * scale) / 2
        offset_y = pad + (avail_h - items_rect.height() * scale) / 2

        def to_mini(scene_x, scene_y):
            mx = offset_x + (scene_x - items_rect.left()) * scale
            my = offset_y + (scene_y - items_rect.top()) * scale
            return mx, my

        for item in self.scene.items():
            if isinstance(item, BaseNode):
                theme = BaseNode.NODE_THEME.get(item.title, BaseNode.DEFAULT_THEME)
                r = item.boundingRect()
                pos = item.pos()
                mx, my = to_mini(pos.x() + r.x(), pos.y() + r.y())
                mw = max(r.width() * scale, 4)
                mh = max(r.height() * scale, 3)
                painter.setPen(QPen(QColor(theme["border"]), 0.5))
                painter.setBrush(QBrush(QColor(theme["bg"])))
                painter.drawRoundedRect(QRectF(mx, my, mw, mh), 1, 1)

        vp_rect = self.view.viewport().rect()
        tl = self.view.mapToScene(vp_rect.topLeft())
        br = self.view.mapToScene(vp_rect.bottomRight())
        vtl_x, vtl_y = to_mini(tl.x(), tl.y())
        vbr_x, vbr_y = to_mini(br.x(), br.y())
        painter.setPen(QPen(QColor("#4078c8"), 1))
        painter.setBrush(QBrush(QColor(64, 120, 200, 30)))
        painter.drawRect(QRectF(vtl_x, vtl_y, vbr_x - vtl_x, vbr_y - vtl_y))
        painter.end()

    def mousePressEvent(self, event):
        self._pan_to(event.position())
        event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._pan_to(event.position())

    def _pan_to(self, pos):
        items_rect = self.scene.itemsBoundingRect()
        if items_rect.isNull():
            return
        pad = self.PADDING
        avail_w = self.WIDTH - pad * 2
        avail_h = self.HEIGHT - pad * 2
        scale_x = avail_w / max(items_rect.width(), 1)
        scale_y = avail_h / max(items_rect.height(), 1)
        scale = min(scale_x, scale_y) * 0.9
        offset_x = pad + (avail_w - items_rect.width() * scale) / 2
        offset_y = pad + (avail_h - items_rect.height() * scale) / 2
        scene_x = items_rect.left() + (pos.x() - offset_x) / scale
        scene_y = items_rect.top() + (pos.y() - offset_y) / scale
        self.view.centerOn(QPointF(scene_x, scene_y))
