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
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QDesktopServices

from core.settings_manager import SettingsManager
from core.i18n import t

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
        self.setWindowTitle(t("settings_title"))
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
        self._cat_keys = ("settings_cat_language", "settings_cat_theme", "settings_cat_general", "settings_cat_contact")
        for key in self._cat_keys:
            self._categories.addItem(QListWidgetItem(t(key)))
        self._categories.currentRowChanged.connect(self._on_category_changed)
        layout.addWidget(self._categories)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._page_language())
        self._stack.addWidget(self._page_theme())
        self._stack.addWidget(self._page_general())
        self._stack.addWidget(self._page_contact())
        layout.addWidget(self._stack, 1)

        bottom = QVBoxLayout()
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._close_btn = QPushButton(t("settings_close"))
        self._close_btn.clicked.connect(self.accept)
        btn_row.addWidget(self._close_btn)
        bottom.addLayout(btn_row)

        outer = QVBoxLayout()
        outer.addLayout(layout, 1)
        outer.addLayout(bottom)
        self.setLayout(outer)

    def _page_language(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self._lang_title = QLabel(t("settings_app_language"))
        layout.addWidget(self._lang_title)
        self._lang_combo = QComboBox()
        self._lang_combo.addItems([t("lang_combo_tr"), t("lang_combo_en")])
        layout.addWidget(self._lang_combo)
        self._lang_hint = QLabel(t("settings_lang_restart_hint"))
        layout.addWidget(self._lang_hint)
        self._apply_lang_btn = QPushButton(t("settings_apply"))
        self._apply_lang_btn.clicked.connect(self._apply_language)
        layout.addWidget(self._apply_lang_btn)
        self._restart_btn = QPushButton(t("settings_restart_now"))
        self._restart_btn.clicked.connect(self._restart_app)
        layout.addWidget(self._restart_btn)
        layout.addStretch()
        return page

    def _page_theme(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self._theme_title = QLabel(t("settings_color_theme"))
        layout.addWidget(self._theme_title)
        self._theme_group = QButtonGroup(self)
        theme_box = QGroupBox()
        theme_layout = QVBoxLayout(theme_box)
        self._theme_radios: list[tuple[str, QRadioButton]] = []
        theme_keys = ("dark", "light", "ocean")
        theme_label_keys = ("theme_dark", "theme_light", "theme_ocean")
        current = self._sm.get("theme", "dark")
        for key, label_key in zip(theme_keys, theme_label_keys):
            row = QHBoxLayout()
            radio = QRadioButton(t(label_key))
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
            self._theme_radios.append((label_key, radio))
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
        self._welcome_cb = QCheckBox(t("settings_welcome_startup"))
        self._tour_cb = QCheckBox(t("settings_tour_startup"))
        self._autosave_cb = QCheckBox(t("settings_autosave"))
        self._autosave_cb.setEnabled(False)
        layout.addWidget(self._welcome_cb)
        layout.addWidget(self._tour_cb)
        layout.addWidget(self._autosave_cb)
        self._reset_btn = QPushButton(t("settings_reset_defaults"))
        self._reset_btn.clicked.connect(self._reset_defaults)
        layout.addWidget(self._reset_btn)
        layout.addStretch()
        return page

    def _page_contact(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        
        self._contact_title = QLabel(t("settings_contact_title"))
        contact_title_font = QFont()
        contact_title_font.setPointSize(12)
        contact_title_font.setBold(True)
        self._contact_title.setFont(contact_title_font)
        layout.addWidget(self._contact_title)
        
        self._contact_desc = QLabel(t("settings_contact_description"))
        self._contact_desc.setWordWrap(True)
        self._contact_desc.setStyleSheet(f"color: #aaa; margin-top: 8px; margin-bottom: 16px;")
        layout.addWidget(self._contact_desc)
        
        # İletişim linki butonu
        self._contact_btn = QPushButton("📧 https://erkanturgut.com/contact")
        self._contact_btn.setStyleSheet(f"""
            QPushButton {{
                background: #2a5cbf;
                color: white;
                border: 1px solid #4078c8;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{ background: #3a6fcf; }}
            QPushButton:pressed {{ background: #1a4caf; }}
        """)
        self._contact_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://erkanturgut.com/contact"))
        )
        layout.addWidget(self._contact_btn)
        
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
        self._retranslate_ui()
        parent = self.parent()
        if parent and hasattr(parent, "_apply_ui_strings"):
            parent._apply_ui_strings()
            parent.statusbar.showMessage(t("lang_applied"), 3000)

    def _retranslate_ui(self):
        self.setWindowTitle(t("settings_title"))
        for i, key in enumerate(self._cat_keys):
            self._categories.item(i).setText(t(key))
        self._lang_title.setText(t("settings_app_language"))
        self._lang_hint.setText(t("settings_lang_restart_hint"))
        self._theme_title.setText(t("settings_color_theme"))
        self._welcome_cb.setText(t("settings_welcome_startup"))
        self._tour_cb.setText(t("settings_tour_startup"))
        self._autosave_cb.setText(t("settings_autosave"))
        self._apply_lang_btn.setText(t("settings_apply"))
        self._restart_btn.setText(t("settings_restart_now"))
        self._close_btn.setText(t("settings_close"))
        self._reset_btn.setText(t("settings_reset_defaults"))
        # İletişim sayfası attribute'leri varsa güncelle
        if hasattr(self, "_contact_title"):
            self._contact_title.setText(t("settings_contact_title"))
        if hasattr(self, "_contact_desc"):
            self._contact_desc.setText(t("settings_contact_description"))
        idx = self._lang_combo.currentIndex()
        self._lang_combo.blockSignals(True)
        self._lang_combo.clear()
        self._lang_combo.addItems([t("lang_combo_tr"), t("lang_combo_en")])
        self._lang_combo.setCurrentIndex(idx)
        self._lang_combo.blockSignals(False)
        for label_key, radio in self._theme_radios:
            radio.setText(t(label_key))

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
