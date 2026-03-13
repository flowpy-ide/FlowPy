# models/node.py
# ──────────────────────────────────────────────────────────────────────
# BaseNode  : QGraphicsItem tabanlı sürüklenebilir düğüm.
# Port      : Düğümlerin giriş/çıkış bağlantı noktaları.
# ──────────────────────────────────────────────────────────────────────

from PyQt6.QtWidgets import QGraphicsItem, QGraphicsEllipseItem
from PyQt6.QtCore import QRectF, Qt, QPointF
from PyQt6.QtGui import (QPainter, QColor, QPen, QBrush, QFont,
                         QLinearGradient)


# ═══════════════════════════════════════════════════════════════════════
#  Port (Bağlantı Noktası)
# ═══════════════════════════════════════════════════════════════════════

class Port(QGraphicsEllipseItem):
    """Düğüm üzerindeki giriş veya çıkış bağlantı noktası."""

    RADIUS = 6  # piksel

    def __init__(self, parent_node, is_output: bool = False):
        diameter = self.RADIUS * 2
        super().__init__(-self.RADIUS, -self.RADIUS, diameter, diameter,
                         parent_node)
        self.is_output = is_output

        # Görsel ayarlar
        self._base_color = QColor("#2ecc71") if is_output else QColor("#3498db")
        self.setBrush(QBrush(self._base_color))
        self.setPen(QPen(QColor("#2c3e50"), 1.5))
        self.setCursor(Qt.CursorShape.CrossCursor)

        # Hover efekti için bayraklar
        self.setAcceptHoverEvents(True)

    # ── Hover Efektleri ──────────────────────────────────────────────

    def hoverEnterEvent(self, event):
        """Port üzerine gelindiğinde büyüt ve parlat."""
        self.setBrush(QBrush(QColor("#f1c40f")))  # Altın sarısı
        self.setScale(1.4)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Port'tan ayrıldığında eski haline döndür."""
        self.setBrush(QBrush(self._base_color))
        self.setScale(1.0)
        super().hoverLeaveEvent(event)

    # ── Fare Olayları (Bağlantı İçin) ────────────────────────────────

    def mousePressEvent(self, event):
        """Porta tıklandığında bağlantı çizimini başlat."""
        if event.button() == Qt.MouseButton.LeftButton:
            scene = self.scene()
            if scene and hasattr(scene, 'start_connection'):
                scene.start_connection(self)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Sürükleme sırasında geçici çizgiyi güncelle."""
        scene = self.scene()
        if scene and hasattr(scene, 'update_connection'):
            scene.update_connection(event.scenePos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Bırakıldığında bağlantıyı tamamla veya iptal et."""
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

    # Düğüm boyutları
    WIDTH = 140
    HEIGHT = 64
    CORNER_RADIUS = 12

    # Düğüm tiplerine göre renk paleti
    COLOR_MAP = {
        "Start":    ("#27ae60", "#2ecc71"),   # Yeşil
        "Process":  ("#2980b9", "#3498db"),   # Mavi
        "Decision": ("#8e44ad", "#9b59b6"),   # Mor
    }
    DEFAULT_COLORS = ("#2c3e50", "#34495e")    # Koyu gri (bilinmeyen tipler)

    def __init__(self, title: str = "Process", node_id: str = ""):
        super().__init__()
        self.title = title
        self.node_id = node_id          # Registry tarafından atanır

        # ── Bayraklar ─────────────────────────────────────────────────
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

        # ── Portlar ──────────────────────────────────────────────────
        self.input_ports: list[Port] = []
        self.output_ports: list[Port] = []

        # Varsayılan olarak 1 giriş + 1 çıkış portu oluştur
        self._create_default_ports()

        # Bu düğüme bağlı tüm Edge nesneleri
        self.edges: list = []

    # ── Port Yardımcıları ────────────────────────────────────────────

    def _create_default_ports(self):
        """1 giriş (sol) + 1 çıkış (sağ) portu oluşturur."""
        # Giriş portu — sol kenar, dikey orta
        inp = Port(self, is_output=False)
        inp.setPos(0, self.HEIGHT / 2)
        self.input_ports.append(inp)

        # Çıkış portu — sağ kenar, dikey orta
        out = Port(self, is_output=True)
        out.setPos(self.WIDTH, self.HEIGHT / 2)
        self.output_ports.append(out)

    # ── QGraphicsItem Zorunlu Metotları ──────────────────────────────

    def boundingRect(self) -> QRectF:
        """Düğümün tıklanabilir / çizilebilir sınır dikdörtgeni."""
        return QRectF(0, 0, self.WIDTH, self.HEIGHT)

    def paint(self, painter: QPainter, option, widget=None):
        """Düğümün görsel çizimi — gradient, yuvarlak köşeler, başlık."""
        rect = self.boundingRect()

        # Renk paletini seç
        dark, light = self.COLOR_MAP.get(self.title, self.DEFAULT_COLORS)

        # ── Gradient arka plan ────────────────────────────────────────
        gradient = QLinearGradient(0, 0, 0, self.HEIGHT)
        gradient.setColorAt(0, QColor(light))
        gradient.setColorAt(1, QColor(dark))
        painter.setBrush(QBrush(gradient))

        # ── Kenarlık ─────────────────────────────────────────────────
        if self.isSelected():
            painter.setPen(QPen(QColor("#f1c40f"), 3))   # Altın sarısı seçim
        else:
            painter.setPen(QPen(QColor("#2c3e50"), 1.5))

        painter.drawRoundedRect(rect, self.CORNER_RADIUS, self.CORNER_RADIUS)

        # ── Başlık Metni ─────────────────────────────────────────────
        font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.title)

    # ── Konum Değişikliği → Edge Güncelleme ──────────────────────────

    def itemChange(self, change, value):
        """Düğüm sürüklendiğinde bağlı okları yeniden çizer."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            for edge in self.edges:
                edge.update_path()
        return super().itemChange(change, value)
