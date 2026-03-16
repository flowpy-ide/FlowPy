# models/node.py
# ──────────────────────────────────────────────────────────────────────
# BaseNode  : QGraphicsItem tabanlı sürüklenebilir düğüm.
# Port      : Düğümlerin giriş/çıkış bağlantı noktaları.
# ──────────────────────────────────────────────────────────────────────

from PyQt6.QtWidgets import QGraphicsItem, QGraphicsEllipseItem, QGraphicsDropShadowEffect
from PyQt6.QtCore import QRectF, Qt, QPointF
from PyQt6.QtGui import (QPainter, QColor, QPen, QBrush, QFont,
                         QLinearGradient)


# ═══════════════════════════════════════════════════════════════════════
#  Port (Bağlantı Noktası)
# ═══════════════════════════════════════════════════════════════════════

class Port(QGraphicsEllipseItem):
    """Düğüm üzerindeki giriş veya çıkış bağlantı noktası."""

    RADIUS = 6  # piksel

    def __init__(self, parent_node, is_output: bool = False, label: str = ""):
        diameter = self.RADIUS * 2
        super().__init__(-self.RADIUS, -self.RADIUS, diameter, diameter,
                         parent_node)
        self.is_output = is_output
        self.label = label  # Opsiyonel etiket (ör: "True", "False")

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

# Düğüm tiplerine göre varsayılan özellikler
_DEFAULT_PROPERTIES = {
    "Start":    {"variables": ""},
    "Process":  {"code": "", "description": ""},
    "Decision": {"condition": "", "description": ""},
    "While":    {"condition": "", "description": ""},
    "Input":    {"variable": "USER_IN", "prompt": "Değer girin:"},
    "Output":   {"expression": ""},
    "For":      {"variable": "i", "start": "0", "end": "10", "step": "1"},
    "Function": {"function_name": "my_func", "parameters": ""},
    "Return":   {"expression": ""},
}


class BaseNode(QGraphicsItem):
    """Sahneye yerleştirilebilen, sürüklenebilir temel düğüm."""

    # Düğüm boyutları
    WIDTH = 160
    HEIGHT = 80
    CORNER_RADIUS = 12

    # Düğüm tiplerine göre renk paleti
    COLOR_MAP = {
        "Start":    ("#27ae60", "#2ecc71"),   # Yeşil
        "Process":  ("#2980b9", "#3498db"),   # Mavi
        "Decision": ("#8e44ad", "#9b59b6"),   # Mor
        "While":    ("#d35400", "#e67e22"),   # Turuncu
        "For":      ("#d35400", "#e67e22"),   # Turuncu (Döngü)
        "Input":    ("#16a085", "#1abc9c"),   # Teal
        "Output":   ("#c0392b", "#e74c3c"),   # Kırmızı
        "Function": ("#2c3e50", "#34495e"),   # Koyu mavi
        "Return":   ("#7f8c8d", "#95a5a6"),   # Gri
    }
    DEFAULT_COLORS = ("#2c3e50", "#34495e")    # Koyu gri (bilinmeyen tipler)

    def __init__(self, title: str = "Process", node_id: str = ""):
        super().__init__()
        self.title = title
        self.node_id = node_id          # Registry tarafından atanır

        # ── Özellikler (properties) ──────────────────────────────────
        defaults = _DEFAULT_PROPERTIES.get(title, {})
        self.properties: dict = dict(defaults)  # kopya

        # ── Bayraklar ─────────────────────────────────────────────────
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

        # ── Portlar ──────────────────────────────────────────────────
        self.input_ports: list[Port] = []
        self.output_ports: list[Port] = []

        # Tip bazlı port yapısı
        self._create_ports()

        # Bu düğüme bağlı tüm Edge nesneleri
        self.edges: list = []

        # Çalıştırma sırasında vurgulama bayrağı
        self._highlight_active = False

        # Görsel Glow Efekti (Çalıştırma sırasında)
        self.glow_effect = QGraphicsDropShadowEffect()
        self.glow_effect.setBlurRadius(25)
        self.glow_effect.setColor(QColor("#f39c12")) # Turuncu glow
        self.glow_effect.setOffset(0, 0)
        self.glow_effect.setEnabled(False)
        self.setGraphicsEffect(self.glow_effect)

    def set_highlight(self, active: bool):
        """Çalıştırılan düğümü görsel olarak parlatır (glow)."""
        self._highlight_active = active
        self.glow_effect.setEnabled(active)
        self.update()

    # ── Port Yardımcıları ────────────────────────────────────────────

    def _create_ports(self):
        """Düğüm tipine göre portları oluşturur."""
        if self.title == "Decision":
            # Decision: 1 giriş (sol), 2 çıkış (sağ üst ✓ / sağ alt ✗)
            inp = Port(self, is_output=False)
            inp.setPos(0, self.HEIGHT / 2)
            self.input_ports.append(inp)

            out_true = Port(self, is_output=True, label="True")
            out_true._base_color = QColor("#2ecc71")  # Yeşil
            out_true.setBrush(QBrush(out_true._base_color))
            out_true.setPos(self.WIDTH, self.HEIGHT * 0.3)
            self.output_ports.append(out_true)

            out_false = Port(self, is_output=True, label="False")
            out_false._base_color = QColor("#e74c3c")  # Kırmızı
            out_false.setBrush(QBrush(out_false._base_color))
            out_false.setPos(self.WIDTH, self.HEIGHT * 0.7)
            self.output_ports.append(out_false)

        elif self.title in ("While", "For"):
            # Döngü: 1 giriş (sol), 2 çıkış (üst: 🔁 döngü gövdesi, alt: ➡ çıkış)
            inp = Port(self, is_output=False)
            inp.setPos(0, self.HEIGHT / 2)
            self.input_ports.append(inp)

            out_loop = Port(self, is_output=True, label="Loop")
            out_loop._base_color = QColor("#e67e22")  # Turuncu
            out_loop.setBrush(QBrush(out_loop._base_color))
            out_loop.setPos(self.WIDTH, self.HEIGHT * 0.3)
            self.output_ports.append(out_loop)

            out_exit = Port(self, is_output=True, label="Exit")
            out_exit._base_color = QColor("#1abc9c")  # Turkuaz
            out_exit.setBrush(QBrush(out_exit._base_color))
            out_exit.setPos(self.WIDTH, self.HEIGHT * 0.7)
            self.output_ports.append(out_exit)

        elif self.title == "Start":
            # Start: sadece 1 çıkış (sağ)
            out = Port(self, is_output=True)
            out.setPos(self.WIDTH, self.HEIGHT / 2)
            self.output_ports.append(out)

        else:
            # Process ve diğerleri: 1 giriş + 1 çıkış
            inp = Port(self, is_output=False)
            inp.setPos(0, self.HEIGHT / 2)
            self.input_ports.append(inp)

            out = Port(self, is_output=True)
            out.setPos(self.WIDTH, self.HEIGHT / 2)
            self.output_ports.append(out)

    # ── QGraphicsItem Zorunlu Metotları ──────────────────────────────

    def boundingRect(self) -> QRectF:
        """Düğümün tıklanabilir / çizilebilir sınır dikdörtgeni."""
        return QRectF(0, 0, self.WIDTH, self.HEIGHT)

    def paint(self, painter: QPainter, option, widget=None):
        """Düğümün görsel çizimi — gradient, yuvarlak köşeler, başlık + özellik."""
        rect = self.boundingRect()

        # Renk paletini seç
        dark, light = self.COLOR_MAP.get(self.title, self.DEFAULT_COLORS)

        # ── Gradient arka plan ────────────────────────────────────────
        gradient = QLinearGradient(0, 0, 0, self.HEIGHT)
        gradient.setColorAt(0, QColor(light))
        gradient.setColorAt(1, QColor(dark))
        painter.setBrush(QBrush(gradient))

        # ── Kenarlık ─────────────────────────────────────────────────
        if self._highlight_active:
            # Glow effect zaten var, sadece çerçeveyi de belirginleştir
            painter.setPen(QPen(QColor("#f1c40f"), 3))
        elif self.isSelected():
            painter.setPen(QPen(QColor("#f1c40f"), 3))   # Altın sarısı seçim
        else:
            painter.setPen(QPen(QColor("#2c3e50"), 1.5))

        painter.drawRoundedRect(rect, self.CORNER_RADIUS, self.CORNER_RADIUS)

        # ── Başlık Metni (üst yarı) ─────────────────────────────────
        title_rect = QRectF(0, 4, self.WIDTH, self.HEIGHT / 2)
        font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self.title)

        # ── Özellik Özet Metni (alt yarı) ────────────────────────────
        summary = self._get_property_summary()
        if summary:
            summary_rect = QRectF(8, self.HEIGHT / 2 - 2, self.WIDTH - 16, self.HEIGHT / 2)
            small_font = QFont("Segoe UI", 7)
            painter.setFont(small_font)
            painter.setPen(QPen(QColor("#ecf0f1")))

            # Metni sığdırmak için kısalt
            metrics = painter.fontMetrics()
            elided = metrics.elidedText(summary, Qt.TextElideMode.ElideRight,
                                         int(summary_rect.width()))
            painter.drawText(summary_rect, Qt.AlignmentFlag.AlignCenter, elided)

        # ── Decision / While port etiketleri ──────────────────────────
        if self.title == "Decision":
            label_font = QFont("Segoe UI", 7, QFont.Weight.Bold)
            painter.setFont(label_font)
            painter.setPen(QPen(QColor("#2ecc71")))
            painter.drawText(QRectF(self.WIDTH - 30, self.HEIGHT * 0.3 - 10, 25, 12),
                             Qt.AlignmentFlag.AlignRight, "✓")
            painter.setPen(QPen(QColor("#e74c3c")))
            painter.drawText(QRectF(self.WIDTH - 30, self.HEIGHT * 0.7 - 2, 25, 12),
                             Qt.AlignmentFlag.AlignRight, "✗")
        elif self.title == "While":
            label_font = QFont("Segoe UI", 7, QFont.Weight.Bold)
            painter.setFont(label_font)
            painter.setPen(QPen(QColor("#e67e22")))
            painter.drawText(QRectF(self.WIDTH - 30, self.HEIGHT * 0.3 - 10, 25, 12),
                             Qt.AlignmentFlag.AlignRight, "🔁")
            painter.setPen(QPen(QColor("#1abc9c")))
            painter.drawText(QRectF(self.WIDTH - 30, self.HEIGHT * 0.7 - 2, 25, 12),
                             Qt.AlignmentFlag.AlignRight, "➡")

    def _get_property_summary(self) -> str:
        """Düğüm tipine göre kısa özet metni döndürür."""
        if self.title == "Decision":
            cond = self.properties.get("condition", "")
            return f"if {cond}" if cond else "⚙ Çift tıkla…"
        elif self.title == "While":
            cond = self.properties.get("condition", "")
            return f"while {cond}" if cond else "⚙ Çift tıkla…"
        elif self.title == "Process":
            code = self.properties.get("code", "")
            if code:
                first_line = code.strip().split("\n")[0]
                return first_line
            return "⚙ Çift tıkla…"
        elif self.title == "Start":
            vars_text = self.properties.get("variables", "")
            if vars_text:
                count = len([l for l in vars_text.strip().split("\n") if l.strip()])
                return f"{count} değişken"
            return "▶ Başlangıç"
        return ""

    # ── Çift Tıklama → Düzenleme Diyaloğu ────────────────────────────

    def mouseDoubleClickEvent(self, event):
        """Düğüme çift tıklandığında düzenleme diyaloğunu açar."""
        from views.node_editor_dialog import NodeEditorDialog

        dialog = NodeEditorDialog(self)
        if dialog.exec():
            # Kullanıcı OK'a bastı → özellikleri güncelle
            new_props = dialog.get_properties()
            self.properties.update(new_props)
            self.update()  # Yeniden çizim tetikle
            
            if self.scene() and hasattr(self.scene(), "history_changed"):
                self.scene().history_changed.emit()

    def mouseReleaseEvent(self, event):
        """Sürükleme bırakıldığında durumu kaydeder."""
        super().mouseReleaseEvent(event)
        if self.scene() and hasattr(self.scene(), "history_changed"):
            self.scene().history_changed.emit()

    # ── Konum Değişikliği → Grid Snapping & Edge Güncelleme ──────────

    def itemChange(self, change, value):
        """Düğüm sürüklendiğinde ızgaraya hizalar ve bağlı okları günceller."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Grid Snapping (Izgaraya Hizalama)
            grid_size = 20
            new_pos = value
            x = round(new_pos.x() / grid_size) * grid_size
            y = round(new_pos.y() / grid_size) * grid_size
            snapped_pos = QPointF(x, y)

            # Edge'leri güncelle
            for edge in self.edges:
                edge.update_path()
                
            return snapped_pos
            
        return super().itemChange(change, value)
