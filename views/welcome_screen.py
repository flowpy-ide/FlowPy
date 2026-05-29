# views/welcome_screen.py
# ──────────────────────────────────────────────────────────────────────
# FlowPyWelcomeScreen : İlk açılışta gösterilen çok sayfalı karşılama diyaloğu.
# ──────────────────────────────────────────────────────────────────────

import os

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QWidget, QCheckBox, QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon, QColor

from core.settings_manager import SettingsManager

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
APP_ICON_PATH = os.path.join(BASE_DIR, "docs", "icon-svg.svg")

ACCENT = "#4078c8"
BG = "#1e1e1e"
PANEL = "#2a2a2a"
TEXT = "#dcdcdc"
TEXT_DIM = "#999"


class FlowPyWelcomeScreen(QDialog):
    """FlowPy karşılama ekranı — 3 sayfalık tanıtım ve başlangıç seçimi."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.load_example = False
        self.dont_show_again = False

        self.setFixedSize(560, 400)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._page_index = 0
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)

        self._card = QWidget()
        self._card.setObjectName("welcomeCard")
        card_layout = QVBoxLayout(self._card)
        card_layout.setContentsMargins(28, 24, 28, 20)
        card_layout.setSpacing(12)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 160))
        self._card.setGraphicsEffect(shadow)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._page_welcome())
        self._stack.addWidget(self._page_features())
        self._stack.addWidget(self._page_ready())
        card_layout.addWidget(self._stack, 1)

        self._dots_label = QLabel("●○○")
        self._dots_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._dots_label.setStyleSheet(f"color: {ACCENT}; font-size: 14px; letter-spacing: 4px;")
        card_layout.addWidget(self._dots_label)

        nav = QHBoxLayout()
        self._back_btn = QPushButton("← Geri")
        self._back_btn.clicked.connect(self._go_back)
        self._back_btn.setVisible(False)
        nav.addWidget(self._back_btn)
        nav.addStretch()
        self._next_btn = QPushButton("İleri →")
        self._next_btn.setObjectName("accentBtn")
        self._next_btn.clicked.connect(self._go_next)
        nav.addWidget(self._next_btn)
        card_layout.addLayout(nav)

        outer.addWidget(self._card)

    def _page_welcome(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(10)
        layout.addStretch()

        if os.path.isfile(APP_ICON_PATH):
            icon_lbl = QLabel()
            icon_lbl.setPixmap(QIcon(APP_ICON_PATH).pixmap(64, 64))
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_lbl)
        logo = QLabel("FlowPy")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        logo.setStyleSheet(f"color: {ACCENT};")
        layout.addWidget(logo)

        title = QLabel("Algoritmalarını Görsel Olarak Tasarla")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT};")
        layout.addWidget(title)

        subtitle = QLabel(
            "Kod yazmadan önce düşün. FlowPy ile akışını çiz, Python kodunu gör."
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
        layout.addWidget(subtitle)
        layout.addStretch()
        return page

    def _page_features(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)
        layout.addStretch()

        features = [
            ("🔷", "Düğümleri Sürükle", "Sol panelden canvas'a bırak"),
            ("⚡", "Çalıştır ve İzle", "Adım adım execution, değişkenleri canlı gör"),
            ("🐍", "Python Kodunu Al", "Sağ panelde otomatik üretilen kodu kopyala"),
        ]
        for icon, title, desc in features:
            row = QHBoxLayout()
            icon_lbl = QLabel(icon)
            icon_lbl.setFixedWidth(36)
            icon_lbl.setStyleSheet("font-size: 22px;")
            row.addWidget(icon_lbl)
            text_col = QVBoxLayout()
            t = QLabel(title)
            t.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            t.setStyleSheet(f"color: {TEXT};")
            d = QLabel(desc)
            d.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px;")
            text_col.addWidget(t)
            text_col.addWidget(d)
            row.addLayout(text_col, 1)
            layout.addLayout(row)

        layout.addStretch()
        return page

    def _page_ready(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)
        layout.addStretch()

        msg = QLabel(
            "İlk akışını oluşturmak için hazırsın. "
            "Bir örnek akış ile başlamak ister misin?"
        )
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setStyleSheet(f"color: {TEXT}; font-size: 12px;")
        layout.addWidget(msg)

        btn_row = QHBoxLayout()
        example_btn = QPushButton("📂 Örnek Akış ile Başla")
        example_btn.setObjectName("accentBtn")
        example_btn.clicked.connect(self._accept_with_example)
        empty_btn = QPushButton("Boş Canvas ile Başla")
        empty_btn.clicked.connect(self._accept_empty)
        btn_row.addWidget(example_btn)
        btn_row.addWidget(empty_btn)
        layout.addLayout(btn_row)

        self._dont_show_cb = QCheckBox("Bir daha gösterme")
        self._dont_show_cb.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px;")
        self._dont_show_cb.toggled.connect(
            lambda checked: setattr(self, "dont_show_again", checked)
        )
        layout.addWidget(self._dont_show_cb, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        return page

    def _apply_style(self):
        self.setStyleSheet(f"""
            #welcomeCard {{
                background: {BG};
                border: 1px solid #333;
                border-radius: 12px;
            }}
            QPushButton {{
                background: {PANEL};
                color: {TEXT};
                border: 1px solid #444;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 11px;
            }}
            QPushButton:hover {{ border-color: {ACCENT}; background: #333; }}
            QPushButton#accentBtn {{
                background: {ACCENT};
                color: #fff;
                border: none;
                font-weight: bold;
            }}
            QPushButton#accentBtn:hover {{ background: #5088d8; }}
            QCheckBox {{ color: {TEXT_DIM}; }}
        """)

    def _update_dots(self):
        dots = ["○", "○", "○"]
        for i in range(self._page_index + 1):
            dots[i] = "●"
        self._dots_label.setText("".join(dots))

    def _go_next(self):
        if self._page_index < 2:
            self._page_index += 1
            self._stack.setCurrentIndex(self._page_index)
            self._back_btn.setVisible(self._page_index > 0)
            self._next_btn.setVisible(self._page_index < 2)
            self._update_dots()

    def _go_back(self):
        if self._page_index > 0:
            self._page_index -= 1
            self._stack.setCurrentIndex(self._page_index)
            self._back_btn.setVisible(self._page_index > 0)
            self._next_btn.setVisible(self._page_index < 2)
            self._update_dots()

    def _accept_with_example(self):
        self.load_example = True
        self._finish()

    def _accept_empty(self):
        self.load_example = False
        self._finish()

    def _finish(self):
        sm = SettingsManager.instance()
        sm.set_bool("welcome_shown", True)
        if self.dont_show_again:
            sm.set_bool("show_welcome_on_startup", False)
        self.accept()
