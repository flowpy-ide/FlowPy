# views/guided_tour.py
# ──────────────────────────────────────────────────────────────────────
# GuidedTour : Ana pencere üzerinde adım adım eğitim turu.
# TourTooltip : Tur adımları için balon ipucu penceresi.
# TourOverlay : Hedef widget etrafında vurgu overlay'i.
# ──────────────────────────────────────────────────────────────────────

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QApplication, QToolButton,
)
from PyQt6.QtCore import QObject, Qt, QRect, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

from core.settings_manager import SettingsManager

ACCENT = "#4078c8"
BG = "#2a2a2a"
TEXT = "#ffffff"
TEXT_DIM = "#aaaaaa"


class TourOverlay(QWidget):
    """Ana pencere üzerinde karartma + hedef alan vurgusu."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self._highlight_rect = QRect()
        self.hide()

    def set_highlight_rect(self, rect: QRect):
        self._highlight_rect = rect
        host = self.parentWidget()
        if host:
            self.setGeometry(0, 0, host.width(), host.height())
        self.show()
        self.raise_()
        self.update()

    def clear(self):
        self._highlight_rect = QRect()
        self.hide()

    def paintEvent(self, event):
        if self._highlight_rect.isNull():
            return
        painter = QPainter(self)
        dim = QColor(0, 0, 0, 140)
        full = self.rect()
        r = self._highlight_rect.adjusted(-4, -4, 4, 4)
        painter.fillRect(0, 0, full.width(), r.top(), dim)
        painter.fillRect(0, r.bottom(), full.width(), full.height() - r.bottom(), dim)
        painter.fillRect(0, r.top(), r.left(), r.height(), dim)
        painter.fillRect(r.right(), r.top(), full.width() - r.right(), r.height(), dim)
        pen = QPen(QColor(ACCENT))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(r)
        painter.end()


class TourTooltip(QWidget):
    """Tur adımı için frameless balon ipucu."""

    def __init__(self, parent=None):
        super().__init__(
            parent,
            Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedWidth(300)
        self._build_ui()
        self.setStyleSheet(f"""
            TourTooltip, QWidget#tourTooltipRoot {{
                background: {BG};
                border-left: 3px solid {ACCENT};
                border-radius: 6px;
            }}
            QLabel {{ background: transparent; }}
            QPushButton {{
                background: #333;
                color: {TEXT};
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px 10px;
            }}
            QPushButton#accentBtn {{
                background: {ACCENT};
                color: #fff;
                border: none;
            }}
        """)

    def _build_ui(self):
        root = QWidget(self)
        root.setObjectName("tourTooltipRoot")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(root)

        self.title_label = QLabel()
        self.title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.title_label.setStyleSheet(f"color: {TEXT};")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px;")
        layout.addWidget(self.desc_label)

        footer = QHBoxLayout()
        self.counter_label = QLabel()
        self.counter_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9px;")
        footer.addWidget(self.counter_label)
        footer.addStretch()
        self.skip_btn = QPushButton("Turu Geç")
        self.next_btn = QPushButton("İleri →")
        self.next_btn.setObjectName("accentBtn")
        footer.addWidget(self.skip_btn)
        footer.addWidget(self.next_btn)
        layout.addLayout(footer)

    def set_content(self, title: str, description: str, step: int, total: int):
        self.title_label.setText(title)
        self.desc_label.setText(description)
        self.counter_label.setText(f"[{step} / {total}]")

    def position_near(self, target_rect: QRect, host_rect: QRect):
        margin = 12
        x = target_rect.right() + margin
        y = target_rect.top()
        if x + self.width() > host_rect.right():
            x = max(host_rect.left() + margin,
                    target_rect.left() - self.width() - margin)
        if y + self.height() > host_rect.bottom():
            y = target_rect.bottom() - self.height()
        if y < host_rect.top():
            y = target_rect.bottom() + margin
        self.move(x, y)


class GuidedTour(QObject):
    """7 adımlı eğitim turu yöneticisi."""

    STEPS = [
        ("nodeTreeWidget", "Node Paleti",
         "Buradan düğümleri canvas'a sürükleyebilirsin. Start ile başla!"),
        ("graphicsView", "Canvas",
         "Algoritman buraya çizilir. Düğümleri istediğin yere yerleştir."),
        ("actionRunFlow", "Çalıştır",
         "Akışını test etmek için Run All'a bas. Step ile adım adım ilerle."),
        ("consoleOutput", "Konsol",
         "Her adım burada loglanır. Hangi düğümde ne olduğunu görebilirsin."),
        ("variableTable", "Değişkenler",
         "Çalışma sırasında değişkenlerin değerlerini canlı izle."),
        ("codeGenOutput", "Python Kodu",
         "Çizdiğin akış otomatik olarak Python koduna dönüşür!"),
        (None, "Hazırsın! 🎉",
         "İlk algoritmanı çizmeye başlayabilirsin. Başarılar!"),
    ]

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self._step_index = 0
        self._overlay = TourOverlay(main_window)
        self._tooltip = TourTooltip()
        self._tooltip.next_btn.clicked.connect(self._next_step)
        self._tooltip.skip_btn.clicked.connect(self._skip)

    def start(self):
        self._step_index = 0
        self._show_step()

    def _resolve_target(self, name: str | None):
        if name is None:
            return None
        mw = self.main_window
        if name == "actionRunFlow":
            action = getattr(mw, "actionRunFlow", None)
            if action:
                for btn in mw.findChildren(QToolButton):
                    if btn.defaultAction() is action:
                        return btn
            for tb in mw.findChildren(QWidget):
                if hasattr(tb, "action") and tb.action() is action:
                    return tb
            return mw.toolBar if hasattr(mw, "toolBar") else None
        return getattr(mw, name, None)

    def _target_global_rect(self, widget) -> QRect:
        if widget is None:
            mw = self.main_window
            cx = mw.width() // 2 - 80
            cy = mw.height() // 2 - 40
            top_left = mw.mapToGlobal(QPoint(cx, cy))
            return QRect(top_left.x(), top_left.y(), 160, 80)
        top_left = widget.mapToGlobal(QPoint(0, 0))
        return QRect(top_left.x(), top_left.y(), widget.width(), widget.height())

    def _show_step(self):
        if self._step_index >= len(self.STEPS):
            self._complete()
            return

        target_name, title, desc = self.STEPS[self._step_index]
        widget = self._resolve_target(target_name)
        global_rect = self._target_global_rect(widget)

        local_rect = QRect(
            self.main_window.mapFromGlobal(global_rect.topLeft()),
            global_rect.size(),
        )
        self._overlay.set_highlight_rect(local_rect)
        self._overlay.raise_()

        self._tooltip.set_content(
            title, desc, self._step_index + 1, len(self.STEPS)
        )
        tl = self.main_window.mapToGlobal(QPoint(0, 0))
        host_global = QRect(
            tl.x(), tl.y(),
            self.main_window.width(), self.main_window.height(),
        )
        self._tooltip.position_near(global_rect, host_global)
        self._tooltip.show()
        self._tooltip.raise_()

    def _next_step(self):
        self._step_index += 1
        if self._step_index >= len(self.STEPS):
            self._complete()
        else:
            self._show_step()

    def _skip(self):
        self._complete()

    def _complete(self):
        self._overlay.clear()
        self._tooltip.hide()
        SettingsManager.instance().set_bool("tour_completed", True)

    def restart(self):
        SettingsManager.instance().set_bool("tour_completed", False)
        self.start()
