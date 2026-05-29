# core/i18n.py
# ──────────────────────────────────────────────────────────────────────
# Basit sözlük tabanlı çeviri — t(key) ile UI metinlerine erişim.
# ──────────────────────────────────────────────────────────────────────

from core.settings_manager import SettingsManager

STRINGS = {
    "tr": {
        "app_title": "FlowPy — Modern Algorithm IDE",
        "ready_message": "Hazır — Düğümleri canvas'a sürükle, düzenlemek için çift tıkla.",
        "save": "Kaydet",
        "open": "Aç",
        "save_flow": "💾  Kaydet…",
        "open_flow": "📂  Aç…",
        "undo": "↩️  Geri Al",
        "redo": "↪️  Yinele",
        "run_all": "▶ Tümünü Çalıştır",
        "continue_run": "▶ Devam Et",
        "step": "Adım",
        "stop": "Durdur",
        "zoom_in": "Yakınlaştır",
        "zoom_out": "Uzaklaştır",
        "reset_zoom": "Yakınlaştırmayı Sıfırla",
        "fit_to_flow": "Akışa Sığdır",
        "node_palette": "Düğüm Paleti",
        "inspector": "Denetçi",
        "console_output": "Konsol Çıktısı",
        "properties": "Özellikler",
        "variables": "Değişkenler",
        "code": "Kod",
        "settings": "⚙  Ayarlar…",
        "restart_tour": "🎓 Eğitim Turunu Yeniden Başlat",
        "no_node_selected": "Düğüm Seçilmedi",
        "switched_page": "Sayfa değiştirildi: {page}",
    },
    "en": {
        "app_title": "FlowPy — Modern Algorithm IDE",
        "ready_message": "Ready — Drag nodes to canvas, double-click to edit.",
        "save": "Save",
        "open": "Open",
        "save_flow": "💾  Save…",
        "open_flow": "📂  Open…",
        "undo": "↩️  Undo",
        "redo": "↪️  Redo",
        "run_all": "▶ Run All",
        "continue_run": "▶ Continue",
        "step": "Step",
        "stop": "Stop",
        "zoom_in": "Zoom In",
        "zoom_out": "Zoom Out",
        "reset_zoom": "Reset Zoom",
        "fit_to_flow": "Fit to Flow",
        "node_palette": "Node Palette",
        "inspector": "Inspector",
        "console_output": "Console Output",
        "properties": "Properties",
        "variables": "Variables",
        "code": "Code",
        "settings": "⚙  Settings…",
        "restart_tour": "🎓 Restart Guided Tour",
        "no_node_selected": "No Node Selected",
        "switched_page": "Switched to {page}",
    },
}


def current_language() -> str:
    lang = SettingsManager.instance().get("language", "tr")
    return lang if lang in STRINGS else "tr"


def t(key: str, **kwargs) -> str:
    """Aktif dile göre metin döndürür; format kwargs destekler."""
    lang = current_language()
    text = STRINGS.get(lang, STRINGS["en"]).get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text
