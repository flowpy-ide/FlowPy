# models/edge.py
# ──────────────────────────────────────────────────────────────────────
# Edge : İki düğüm (port) arasında Bezier eğrisiyle çizilen bağlantı oku.
# ──────────────────────────────────────────────────────────────────────

from PyQt6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PyQt6.QtCore import QPointF, Qt, QTimer, QRectF
from PyQt6.QtGui import QPainterPath, QPen, QColor, QFont, QPainter

from models.node import BaseNode, Port


class Edge(QGraphicsPathItem):
    """Kaynak port → Hedef port arasında Bezier eğrisiyle bağlantı çizer."""

    def __init__(self, source_node, dest_node, source_port=None, dest_port=None):
        super().__init__()

        self.source_node = source_node
        self.dest_node = dest_node
        self.source_port = source_port or source_node.output_ports[0]
        self.dest_port = dest_port or dest_node.input_ports[0]

        self.setZValue(-1)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        self.source_node.edges.append(self)
        self.dest_node.edges.append(self)

        self._is_animating = False
        self._dash_offset = 0.0
        self._branch_label = None
        self._branch_color = None
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self._animate_step)

        self.update_path()

    def update_path(self):
        if not self.source_port or not self.dest_port:
            return

        r = Port.RADIUS
        src = self.source_port.scenePos() + QPointF(r, r)
        dst = self.dest_port.scenePos() + QPointF(r, r)

        offset = abs(dst.x() - src.x()) * 0.5
        if offset < 50:
            offset = 50

        ctrl1 = src + QPointF(offset, 0)
        ctrl2 = dst - QPointF(offset, 0)

        path = QPainterPath(src)
        path.cubicTo(ctrl1, ctrl2, dst)
        self.setPath(path)
        self._update_branch_label()

    def _update_branch_label(self):
        self._branch_label = None
        self._branch_color = None
        src = self.source_node
        if not src or src.title != "Decision" or not self.source_port:
            return
        if self.source_port not in src.output_ports:
            return
        port_idx = src.output_ports.index(self.source_port)
        if port_idx == 0:
            self._branch_label = "True ✓"
            self._branch_color = "#4ade80"
        elif port_idx == 1:
            self._branch_label = "False ✗"
            self._branch_color = "#f59e0b"

    def set_animating(self, active: bool):
        self._is_animating = active
        if active:
            self.anim_timer.start(40)
        else:
            self.anim_timer.stop()
            self.update()

    def _animate_step(self):
        self._dash_offset -= 1.5
        self.update()

    def paint(self, painter: QPainter, option, widget=None):
        src_title = self.source_node.title if self.source_node else ""
        theme = BaseNode.NODE_THEME.get(src_title, BaseNode.DEFAULT_THEME)
        edge_color = QColor(theme["glow"])
        edge_color.setAlphaF(0.5)

        if self._is_animating:
            edge_color.setAlphaF(0.9)
            pen = QPen(edge_color, 2.0, Qt.PenStyle.SolidLine)
        elif self.isSelected():
            pen = QPen(QColor("#f1c40f"), 2.5, Qt.PenStyle.SolidLine)
        else:
            pen = QPen(edge_color, 1.5, Qt.PenStyle.SolidLine)

        if self._is_animating:
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setDashOffset(self._dash_offset)

        painter.setPen(pen)
        painter.drawPath(self.path())

        if self._branch_label and self._branch_color:
            mid = self.path().pointAtPercent(0.45)
            painter.save()
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#1a1a1a"))
            label_rect = QRectF(mid.x() - 14, mid.y() - 8, 34, 15)
            painter.drawRoundedRect(label_rect, 3, 3)
            painter.setPen(QColor(self._branch_color))
            font = QFont("Segoe UI", 7, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(
                label_rect, Qt.AlignmentFlag.AlignCenter, self._branch_label
            )
            painter.restore()
        else:
            label = getattr(self.source_port, "label", "")
            if label and label not in ("True", "False"):
                point = self.path().pointAtPercent(0.3)
                if label in ("Loop",):
                    text_color = QColor("#a78bfa")
                elif label in ("Exit",):
                    text_color = QColor("#8b5cf6")
                else:
                    text_color = QColor("#ecf0f1")
                painter.setPen(QPen(text_color))
                painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                painter.drawText(
                    QRectF(point.x() - 25, point.y() - 15, 50, 30),
                    Qt.AlignmentFlag.AlignCenter, label,
                )
