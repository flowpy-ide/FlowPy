# views/variable_chart.py
# ──────────────────────────────────────────────────────────────────────
# VariableSparklinePanel : Sayısal değişkenler için miniature trend grafikleri.
# ──────────────────────────────────────────────────────────────────────

import math

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath, QFont, QBrush

SPARKLINE_COLORS = [
    "#4078c8", "#22c55e", "#f59e0b", "#a78bfa",
    "#f472b6", "#60a5fa", "#4ade80", "#fbbf24",
]


class SparklineWidget(QWidget):
    """Tek bir değişken için miniature trend grafiği."""

    HEIGHT = 36
    MAX_POINTS = 30

    def __init__(self, var_name: str, color: str = "#4078c8", parent=None):
        super().__init__(parent)
        self.var_name = var_name
        self.color = QColor(color)
        self.values: list[float] = []
        self.setFixedHeight(self.HEIGHT + 20)
        self.setMinimumWidth(100)

    def add_value(self, value: float):
        self.values.append(value)
        if len(self.values) > self.MAX_POINTS:
            self.values.pop(0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.HEIGHT

        painter.setPen(QColor("#888"))
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        painter.drawText(QRectF(0, 0, w, 14), Qt.AlignmentFlag.AlignLeft, self.var_name)

        if self.values:
            painter.setPen(self.color)
            font.setBold(True)
            painter.setFont(font)
            last = self.values[-1]
            display = round(last, 3) if isinstance(last, float) else last
            painter.drawText(
                QRectF(0, 0, w, 14), Qt.AlignmentFlag.AlignRight, str(display)
            )

        if len(self.values) < 2:
            painter.end()
            return

        chart_y = 16
        chart_h = h - 2
        mn, mx = min(self.values), max(self.values)
        rng = mx - mn if mx != mn else 1

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#1a1a1a"))
        painter.drawRoundedRect(0, chart_y, w, chart_h, 3, 3)

        path = QPainterPath()
        step = w / (len(self.values) - 1)
        for i, v in enumerate(self.values):
            x = i * step
            y = chart_y + chart_h - ((v - mn) / rng) * (chart_h - 4) - 2
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        pen = QPen(self.color, 1.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        last_x = (len(self.values) - 1) * step
        last_v = self.values[-1]
        last_y = chart_y + chart_h - ((last_v - mn) / rng) * (chart_h - 4) - 2
        painter.setBrush(QBrush(self.color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(last_x, last_y), 3, 3)
        painter.end()


def _coerce_chart_value(value) -> float | None:
    """int/float → grafik değeri; çok büyük int'lerde taşmayı önler."""
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, int):
        try:
            f = float(value)
            return f if math.isfinite(f) else None
        except OverflowError:
            if value == 0:
                return 0.0
            # Faktöriyel vb. — log ölçeğiyle trend göster, çökme yok
            return math.copysign(math.log10(abs(value)), value)
    return None


class VariableSparklinePanel(QWidget):
    """Tüm sayısal değişkenlerin sparkline'larını gösteren panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 4, 8, 4)
        self._layout.setSpacing(4)
        self._sparklines: dict[str, SparklineWidget] = {}
        self._color_idx = 0
        self._stretch_added = False

        self._empty_label = QLabel(
            "Henüz değişken yok.\nFlow çalıştırıldığında\nsayısal değişkenler burada görünür."
        )
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #3a3a3a; font-size: 11px;")
        self._layout.addWidget(self._empty_label)
        self._layout.addStretch()
        self._stretch_added = True

    def update_scope(self, scope: dict):
        numeric_vars = {
            k: v for k, v in scope.items()
            if not k.startswith("__") and isinstance(v, (int, float))
        }
        if not numeric_vars:
            return

        if self._empty_label.isVisible():
            self._empty_label.hide()
            if self._stretch_added:
                item = self._layout.itemAt(self._layout.count() - 1)
                if item and item.spacerItem():
                    self._layout.removeItem(item)
                    self._stretch_added = False

        for name, value in numeric_vars.items():
            if name not in self._sparklines:
                color = SPARKLINE_COLORS[self._color_idx % len(SPARKLINE_COLORS)]
                self._color_idx += 1
                spark = SparklineWidget(name, color, self)
                self._sparklines[name] = spark
                self._layout.addWidget(spark)
            chart_val = _coerce_chart_value(value)
            if chart_val is None:
                continue
            self._sparklines[name].add_value(chart_val)

    def reset(self):
        for spark in self._sparklines.values():
            spark.values.clear()
            spark.update()
