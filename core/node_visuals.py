# core/node_visuals.py
# ──────────────────────────────────────────────────────────────────────
# Düğüm şekli ve palet sembolleri — tek kaynak.
# shape: rect | diamond | loop | terminal | parallelogram | document | note | subroutine
# ──────────────────────────────────────────────────────────────────────

from PyQt6.QtCore import QRectF, QPointF, Qt
from PyQt6.QtGui import (
    QBrush, QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap,
)

# shape + palet ikonu (ASCII; canvas üzerinde sembol çizilmez)
NODE_VISUALS: dict[str, dict[str, str]] = {
    # Basic
    "Start":              {"shape": "terminal",       "symbol": "St"},
    "Process":            {"shape": "rect",           "symbol": "Px"},
    "Decision":           {"shape": "diamond",        "symbol": "?"},
    "Stop":               {"shape": "terminal_stop", "symbol": "Sp"},
    "Comment":            {"shape": "note",           "symbol": "//"},
    # Veri
    "Variable":           {"shape": "rect",           "symbol": "V"},
    "Math":               {"shape": "rect",           "symbol": "+"},
    "String Operation":   {"shape": "rect",           "symbol": "Aa"},
    "Type Cast":          {"shape": "rect",           "symbol": "::"},
    "List Operation":     {"shape": "rect",           "symbol": "[]"},
    # Flow
    "While":              {"shape": "loop",           "symbol": "W"},
    "For":                {"shape": "loop",           "symbol": "F"},
    "If Elif Else":       {"shape": "diamond",        "symbol": "If"},
    "Break":              {"shape": "terminal_stop",  "symbol": "Bk"},
    "Continue":           {"shape": "loop",           "symbol": "Cn"},
    "Try Except":         {"shape": "subroutine",     "symbol": "Te"},
    "Switch Match":       {"shape": "diamond",        "symbol": "Sw"},
    # I/O
    "Input":              {"shape": "parallelogram",  "symbol": "In"},
    "Output":             {"shape": "parallelogram",  "symbol": "Out"},
    "Print":              {"shape": "parallelogram",  "symbol": "Pr"},
    "File Read":          {"shape": "document",       "symbol": "Rd"},
    "File Write":         {"shape": "document",       "symbol": "Wr"},
    "Random":             {"shape": "rect",           "symbol": "R"},
    "Delay":              {"shape": "loop",           "symbol": "Dt"},
    # Algoritma
    "Sort":               {"shape": "rect",           "symbol": "So"},
    "Search":             {"shape": "diamond",        "symbol": "Se"},
    "Swap":               {"shape": "rect",           "symbol": "Sw"},
    "Accumulate":         {"shape": "rect",           "symbol": "Ac"},
    # Fonksiyon
    "Function":           {"shape": "subroutine",     "symbol": "Fn"},
    "Return":             {"shape": "rect",           "symbol": "Rt"},
    "Lambda":             {"shape": "subroutine",     "symbol": "Lm"},
    # İleri
    "List Comprehension": {"shape": "rect",           "symbol": "Lc"},
    "Assert":             {"shape": "diamond",        "symbol": "As"},
    "Import":             {"shape": "rect",           "symbol": "Im"},
    "Group":              {"shape": "note",           "symbol": "Gr"},
}

DEFAULT_VISUAL = {"shape": "rect", "symbol": ""}

# Canvas düğümlerinde sol üst sembol/emoji gösterilmez (yalnızca palet ikonunda)
SHOW_SYMBOL_ON_CANVAS = False


def get_node_shape(title: str) -> str:
    return NODE_VISUALS.get(title, DEFAULT_VISUAL)["shape"]


def get_node_symbol(title: str) -> str:
    return NODE_VISUALS.get(title, DEFAULT_VISUAL)["symbol"]


def build_shape_path(shape: str, rect: QRectF, corner_radius: float = 10) -> QPainterPath:
    """Canvas düğüm gövdesi için QPainterPath üretir."""
    path = QPainterPath()
    w, h = rect.width(), rect.height()
    m = 3.0
    r = rect.adjusted(m, m, -m, -m)
    cx, cy = r.center().x(), r.center().y()

    if shape == "diamond":
        path.moveTo(cx, r.top())
        path.lineTo(r.right(), cy)
        path.lineTo(cx, r.bottom())
        path.lineTo(r.left(), cy)
        path.closeSubpath()

    elif shape == "loop":
        path.addEllipse(r)

    elif shape == "terminal":
        path.addRoundedRect(r, h / 2.2, h / 2.2)

    elif shape == "terminal_stop":
        path.addRoundedRect(r, 6, 6)

    elif shape == "parallelogram":
        skew = min(18.0, w * 0.12)
        path.moveTo(r.left() + skew, r.top())
        path.lineTo(r.right(), r.top())
        path.lineTo(r.right() - skew, r.bottom())
        path.lineTo(r.left(), r.bottom())
        path.closeSubpath()

    elif shape == "document":
        fold = 14.0
        body = QRectF(r.left(), r.top(), r.width() - fold * 0.3, r.height())
        path.addRoundedRect(body, 6, 6)
        corner = QPainterPath()
        corner.moveTo(body.right() - fold, body.top())
        corner.lineTo(body.right(), body.top() + fold)
        corner.lineTo(body.right() - fold, body.top() + fold)
        corner.closeSubpath()
        path = path.united(corner)

    elif shape == "note":
        path.addRoundedRect(r, 4, 4)
        tab = QPainterPath()
        tab.addRect(r.right() - 22, r.top() + 4, 18, 14)
        path = path.subtracted(tab)

    elif shape == "subroutine":
        side = min(12.0, w * 0.08)
        inner = r.adjusted(side, 0, -side, 0)
        path.addRoundedRect(inner, corner_radius, corner_radius)
        path.addRect(QRectF(r.left(), r.top() + 8, side, r.height() - 16))
        path.addRect(QRectF(r.right() - side, r.top() + 8, side, r.height() - 16))

    else:
        path.addRoundedRect(r, corner_radius, corner_radius)

    return path


def _draw_palette_shape(painter: QPainter, shape: str, color: QColor):
    """16×16 palet ikonu arka plan şekli."""
    painter.setBrush(color)
    painter.setPen(Qt.PenStyle.NoPen)
    if shape == "diamond":
        pts = [QPointF(8, 1), QPointF(15, 8), QPointF(8, 15), QPointF(1, 8)]
        painter.drawPolygon(pts)
    elif shape == "loop":
        painter.drawEllipse(2, 2, 12, 12)
    elif shape in ("terminal", "terminal_stop"):
        painter.drawRoundedRect(2, 4, 12, 10, 5, 5)
    elif shape == "parallelogram":
        pts = [QPointF(4, 3), QPointF(14, 3), QPointF(12, 13), QPointF(2, 13)]
        painter.drawPolygon(pts)
    elif shape == "document":
        painter.drawRoundedRect(2, 2, 11, 12, 2, 2)
    elif shape == "note":
        painter.drawRoundedRect(2, 2, 12, 12, 2, 2)
    elif shape == "subroutine":
        painter.drawRoundedRect(4, 3, 10, 10, 2, 2)
        painter.drawRect(2, 5, 2, 6)
        painter.drawRect(14, 5, 2, 6)
    else:
        painter.drawRoundedRect(2, 2, 12, 12, 3, 3)


def make_palette_icon(hex_color: str, title: str) -> QIcon:
    """Palete özel: renkli şekil + sembol."""
    vis = NODE_VISUALS.get(title, DEFAULT_VISUAL)
    shape = vis["shape"]
    symbol = vis["symbol"]

    pixmap = QPixmap(22, 22)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    bg = QColor(hex_color)
    _draw_palette_shape(painter, shape, bg)

    if symbol:
        lum = 0.299 * bg.red() + 0.587 * bg.green() + 0.114 * bg.blue()
        fg = QColor("#ffffff") if lum < 140 else QColor("#111111")
        font = QFont("Segoe UI", 7, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(fg)
        painter.drawText(QRectF(0, 0, 22, 22), Qt.AlignmentFlag.AlignCenter, symbol)

    painter.end()
    return QIcon(pixmap)
