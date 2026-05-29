# core/settings_manager.py
# ──────────────────────────────────────────────────────────────────────
# SettingsManager : QSettings("FlowPy", "FlowPy") için singleton sarmalayıcı.
# ──────────────────────────────────────────────────────────────────────

from PyQt6.QtCore import QSettings


class SettingsManager:
    """Uygulama ayarlarını merkezi olarak okur ve yazar."""

    _instance = None

    def __init__(self):
        self._settings = QSettings("FlowPy", "FlowPy")

    @classmethod
    def instance(cls) -> "SettingsManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get(self, key: str, default=None):
        return self._settings.value(key, default)

    def set(self, key: str, value):
        self._settings.setValue(key, value)

    def get_bool(self, key: str, default: bool = False) -> bool:
        val = self._settings.value(key, default)
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
        return bool(val)

    def set_bool(self, key: str, value: bool):
        self._settings.setValue(key, bool(value))

    def reset_defaults(self):
        """Tüm ayarları varsayılan değerlere döndürür."""
        self._settings.clear()
        self.set_bool("show_welcome_on_startup", True)
        self.set_bool("show_tour_on_startup", True)
        self.set_bool("welcome_shown", False)
        self.set_bool("tour_completed", False)
        self.set("language", "tr")
        self.set("theme", "dark")

    def ensure_defaults(self):
        """İlk çalıştırmada eksik anahtarları tamamlar."""
        defaults = {
            "show_welcome_on_startup": True,
            "show_tour_on_startup": True,
            "welcome_shown": False,
            "tour_completed": False,
            "language": "tr",
            "theme": "dark",
        }
        for key, default in defaults.items():
            if self._settings.value(key) is None:
                if isinstance(default, bool):
                    self.set_bool(key, default)
                else:
                    self.set(key, default)
