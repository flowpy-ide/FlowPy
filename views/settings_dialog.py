# views/settings_dialog.py
# ──────────────────────────────────────────────────────────────────────
# SettingsDialog : Dil, tema ve genel uygulama ayarları diyaloğu.
# ──────────────────────────────────────────────────────────────────────

import sys

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QWidget, QLabel, QComboBox, QRadioButton,
    QButtonGroup, QCheckBox, QPushButton, QGroupBox, QApplication,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core.settings_manager import SettingsManager

ACCENT = "#4078c8"
BG = "#1e1e1e"
PANEL = "#2a2a2a"
TEXT = "#dcdcdc"

THEME_PREVIEWS = {
    "dark": ("#1e1e1e", "#4078c8"),
    "light": ("#f5f5f5", "#2a5cbf"),
    "ocean": ("#0d1b2a", "#00b4d8"),
}


class SettingsDialog(QDialog):
    """Kategorili ayarlar penceresi."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ayarlar")
        self.setMinimumSize(520, 380)
        self._sm = SettingsManager.instance()
        self._pending_lang = self._sm.get("language", "tr")
        self._build_ui()
        self._apply_style()
        self._load_values()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(12)

        self._categories = QListWidget()
        self._categories.setFixedWidth(140)
        for name in ("Dil", "Tema", "Genel"):
            self._categories.addItem(QListWidgetItem(name))
        self._categories.currentRowChanged.connect(self._on_category_changed)
        layout.addWidget(self._categories)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._page_language())
        self._stack.addWidget(self._page_theme())
        self._stack.addWidget(self._page_general())
        layout.addWidget(self._stack, 1)

        bottom = QVBoxLayout()
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        bottom.addLayout(btn_row)

        outer = QVBoxLayout()
        outer.addLayout(layout, 1)
        outer.addLayout(bottom)
        self.setLayout(outer)

    def _page_language(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Uygulama Dili"))
        self._lang_combo = QComboBox()
        self._lang_combo.addItems(["🇹🇷 Türkçe", "🇬🇧 English"])
        layout.addWidget(self._lang_combo)
        layout.addWidget(QLabel(
            "⚠ Dil değişikliği uygulamayı yeniden başlatmayı gerektirir."
        ))
        apply_lang = QPushButton("Uygula")
        apply_lang.clicked.connect(self._apply_language)
        layout.addWidget(apply_lang)
        restart_btn = QPushButton("Şimdi Yeniden Başlat")
        restart_btn.clicked.connect(self._restart_app)
        layout.addWidget(restart_btn)
        layout.addStretch()
        return page

    def _page_theme(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Renk Teması"))
        self._theme_group = QButtonGroup(self)
        theme_box = QGroupBox()
        theme_layout = QVBoxLayout(theme_box)
        themes = [
            ("dark", "🌑 Dark (varsayılan)"),
            ("light", "☀️ Light"),
            ("ocean", "🌊 Ocean"),
        ]
        current = self._sm.get("theme", "dark")
        for key, label in themes:
            row = QHBoxLayout()
            radio = QRadioButton(label)
            radio.setProperty("theme_key", key)
            swatch = QLabel("   ")
            swatch.setFixedSize(28, 18)
            bg, accent = THEME_PREVIEWS[key]
            swatch.setStyleSheet(
                f"background: {bg}; border: 2px solid {accent}; border-radius: 4px;"
            )
            row.addWidget(radio)
            row.addWidget(swatch)
            row.addStretch()
            theme_layout.addLayout(row)
            self._theme_group.addButton(radio)
            if key == current:
                radio.setChecked(True)
            radio.toggled.connect(
                lambda checked, k=key: checked and self._apply_theme(k)
            )
        layout.addWidget(theme_box)
        layout.addStretch()
        return page

    def _page_general(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self._welcome_cb = QCheckBox("Başlangıçta karşılama ekranını göster")
        self._tour_cb = QCheckBox("Başlangıçta eğitim turunu göster")
        self._autosave_cb = QCheckBox("Otomatik kayıt (yakında)")
        self._autosave_cb.setEnabled(False)
        layout.addWidget(self._welcome_cb)
        layout.addWidget(self._tour_cb)
        layout.addWidget(self._autosave_cb)
        reset_btn = QPushButton("Varsayılanlara Sıfırla")
        reset_btn.clicked.connect(self._reset_defaults)
        layout.addWidget(reset_btn)
        layout.addStretch()
        return page

    def _apply_style(self):
        self.setStyleSheet(f"""
            QDialog {{ background: {BG}; color: {TEXT}; }}
            QListWidget {{
                background: {PANEL};
                border: 1px solid #333;
                border-radius: 6px;
            }}
            QListWidget::item:selected {{ background: {ACCENT}; }}
            QGroupBox {{ color: {TEXT}; border: 1px solid #444; margin-top: 8px; }}
            QPushButton {{
                background: {PANEL};
                color: {TEXT};
                border: 1px solid #444;
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{ border-color: {ACCENT}; }}
            QComboBox, QCheckBox {{ color: {TEXT}; }}
        """)

    def _load_values(self):
        lang = self._sm.get("language", "tr")
        self._lang_combo.setCurrentIndex(0 if lang == "tr" else 1)
        self._welcome_cb.setChecked(
            self._sm.get_bool("show_welcome_on_startup", True)
        )
        self._tour_cb.setChecked(
            self._sm.get_bool("show_tour_on_startup", True)
        )

    def _on_category_changed(self, row: int):
        if row >= 0:
            self._stack.setCurrentIndex(row)

    def _apply_language(self):
        idx = self._lang_combo.currentIndex()
        lang = "tr" if idx == 0 else "en"
        self._sm.set("language", lang)
        self._pending_lang = lang

    def _apply_theme(self, theme_name: str):
        self._sm.set("theme", theme_name)
        app = QApplication.instance()
        if app:
            import main
            main.setup_theme(theme_name, app)

    def _restart_app(self):
        self._apply_language()
        app = QApplication.instance()
        if app:
            import os
            from PyQt6.QtCore import QProcess
            QProcess.startDetached(
                sys.executable, [os.path.abspath(sys.argv[0])], os.getcwd()
            )
            app.quit()

    def _reset_defaults(self):
        self._sm.reset_defaults()
        self._load_values()
        self._apply_theme("dark")

    def accept(self):
        self._sm.set_bool(
            "show_welcome_on_startup", self._welcome_cb.isChecked()
        )
        self._sm.set_bool("show_tour_on_startup", self._tour_cb.isChecked())
        if self._welcome_cb.isChecked():
            self._sm.set_bool("welcome_shown", False)
        super().accept()
