# models/edge.py
# ──────────────────────────────────────────────────────────────────────
# Edge : İki düğüm (port) arasında Bezier eğrisiyle çizilen
#         dinamik bağlantı oku.
# ──────────────────────────────────────────────────────────────────────

from PyQt6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PyQt6.QtCore import QPointF, Qt, QTimer, QRectF
from PyQt6.QtGui import QPainterPath, QPen, QColor, QFont, QPainter

class Edge(QGraphicsPathItem):
    """Kaynak port → Hedef port arasında Bezier eğrisiyle bağlantı çizer."""

    def __init__(self, source_node, dest_node, source_port=None, dest_port=None):
        super().__init__()

        self.source_node = source_node
        self.dest_node = dest_node

        # Portlar verilmediyse varsayılan ilk çıkış / ilk giriş portlarını kullan
        self.source_port = source_port or source_node.output_ports[0]
        self.dest_port = dest_port or dest_node.input_ports[0]

        # Çizgi stili
        self.setPen(QPen(QColor("#2980b9"), 2.5))
        # Oklar düğümlerin altında kalsın
        self.setZValue(-1)
        # Seçilebilir yap (silme için)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        # Oku her iki düğümün edge listesine kaydet
        self.source_node.edges.append(self)
        self.dest_node.edges.append(self)

        # Animasyon state
        self._is_animating = False
        self._dash_offset = 0.0
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self._animate_step)

        # İlk çizim
        self.update_path()

    # ── Bezier Eğrisi Güncelleme ─────────────────────────────────────

    def update_path(self):
        """Kaynak ve hedef portların güncel sahne koordinatlarına göre
        Bezier eğrisini yeniden hesaplar."""
        if not self.source_port or not self.dest_port:
            return

        # Portların sahne koordinatlarını al (merkeze offset)
        r = 6  # Port yarıçapı
        src = self.source_port.scenePos() + QPointF(r, r)
        dst = self.dest_port.scenePos() + QPointF(r, r)

        # Kontrol noktaları — yatay mesafenin yarısı kadar kavis
        offset = abs(dst.x() - src.x()) * 0.5
        if offset < 50:
            offset = 50

        ctrl1 = src + QPointF(offset, 0)
        ctrl2 = dst - QPointF(offset, 0)

        # Cubic Bezier yolu oluştur
        path = QPainterPath(src)
        path.cubicTo(ctrl1, ctrl2, dst)
        self.setPath(path)

    # ── Seçim & Animasyon Çizimi ─────────────────────────────────────

    def set_animating(self, active: bool):
        """Çalışma anında kenardaki hareket efektini açar/kapatır."""
        self._is_animating = active
        if active:
            self.anim_timer.start(40)  # 25 FPS
        else:
            self.anim_timer.stop()
            self.update()

    def _animate_step(self):
        self._dash_offset -= 1.5  # Çizgi yönünde kayma
        self.update()

    def paint(self, painter: QPainter, option, widget=None):
        """Standard çizimi ezip, seçim/animasyon efektleri ve etiketleri ekler."""
        pen = QPen(QColor("#2980b9"), 2.5)

        if self._is_animating:
            pen.setColor(QColor("#f39c12"))  # Vurgu turuncusu
            pen.setWidth(4)
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setDashOffset(self._dash_offset)
        elif self.isSelected():
            pen.setColor(QColor("#f1c40f"))  # Seçim sarısı
            pen.setWidth(3.5)

        painter.setPen(pen)
        painter.drawPath(self.path())

        # Eğer kaynak port'un özel bir etiketi varsa (Decision -> True/False)
        label = getattr(self.source_port, "label", "")
        if label:
            # Eğrinin %30 noktasına yazıyı yerleştir (kaynağa yakın)
            point = self.path().pointAtPercent(0.3)
            
            # Etiketin rengi
            if label in ("True", "Loop"):
                text_color = QColor("#2ecc71")
            elif label in ("False", "Exit"):
                text_color = QColor("#e74c3c")
            else:
                text_color = QColor("#ecf0f1")

            painter.setPen(QPen(text_color))
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.drawText(QRectF(point.x() - 25, point.y() - 15, 50, 30),
                             Qt.AlignmentFlag.AlignCenter, label)
