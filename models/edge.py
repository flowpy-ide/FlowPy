# models/edge.py
# ──────────────────────────────────────────────────────────────────────
# Edge : İki düğüm (port) arasında Bezier eğrisiyle çizilen
#         dinamik bağlantı oku.
# ──────────────────────────────────────────────────────────────────────

from PyQt6.QtWidgets import QGraphicsPathItem
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPainterPath, QPen, QColor


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

        # Oku her iki düğümün edge listesine kaydet
        self.source_node.edges.append(self)
        self.dest_node.edges.append(self)

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
