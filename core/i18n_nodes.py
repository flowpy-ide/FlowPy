# core/i18n_nodes.py
# Düğüm paleti, özellik alanları ve kategori çevirileri.

import re

from core.i18n import current_language

# Kategori anahtarı → node title listesi (sürükle-bırak ID'leri İngilizce kalır)
NODE_CATEGORIES = {
    "cat_basic": [
        "Start", "Process", "Decision", "Stop", "Comment",
    ],
    "cat_data": [
        "Variable", "Math", "String Operation", "Type Cast", "List Operation",
    ],
    "cat_flow": [
        "While", "For", "If Elif Else", "Break", "Continue",
        "Try Except", "Switch Match",
    ],
    "cat_io": [
        "Input", "Output", "Print", "File Read", "File Write", "Random", "Delay",
    ],
    "cat_algorithms": [
        "Sort", "Search", "Swap", "Accumulate",
    ],
    "cat_functions": [
        "Function", "Return", "Lambda",
    ],
    "cat_advanced": [
        "List Comprehension", "Assert", "Import", "Group",
    ],
}

NODE_STRINGS: dict[str, dict[str, str]] = {
    "tr": {
        # Kategoriler
        "cat_basic": "Temel",
        "cat_data": "Veri & Değişken",
        "cat_flow": "Akış Kontrolü",
        "cat_io": "G/Ç",
        "cat_algorithms": "Algoritmalar",
        "cat_functions": "Fonksiyonlar",
        "cat_advanced": "İleri Seviye",
        # Düğüm adları (palet)
        "node_start": "Başlangıç",
        "node_process": "İşlem",
        "node_decision": "Karar",
        "node_stop": "Durdur",
        "node_comment": "Yorum",
        "node_variable": "Değişken",
        "node_math": "Matematik",
        "node_string_operation": "Metin İşlemi",
        "node_type_cast": "Tip Dönüşümü",
        "node_list_operation": "Liste İşlemi",
        "node_while": "While Döngüsü",
        "node_for": "For Döngüsü",
        "node_if_elif_else": "If / Elif / Else",
        "node_break": "Break",
        "node_continue": "Continue",
        "node_try_except": "Try / Except",
        "node_switch_match": "Switch / Match",
        "node_input": "Girdi",
        "node_output": "Çıktı",
        "node_print": "Yazdır",
        "node_file_read": "Dosya Oku",
        "node_file_write": "Dosya Yaz",
        "node_random": "Rastgele",
        "node_delay": "Bekleme",
        "node_sort": "Sırala",
        "node_search": "Ara",
        "node_swap": "Takas",
        "node_accumulate": "Biriktir",
        "node_function": "Fonksiyon",
        "node_return": "Return",
        "node_lambda": "Lambda",
        "node_list_comprehension": "Liste Üretimi",
        "node_assert": "Assert",
        "node_import": "Import",
        "node_group": "Grup",
        # Diyalog
        "dialog_edit_node": "Düğüm Düzenle — {name}",
        "dialog_node_title": "📦  {name} Düğümü",
        "dialog_properties": "Özellikler",
        "hint_double_click": "⚙ Çift tıkla…",
        "hint_start": "▶ Başlangıç",
        "hint_var_count": "{n} değişken",
        # Ortak alan etiketleri
        "prop_description": "Açıklama",
        "prop_condition": "Koşul İfadesi",
        "prop_loop_condition": "Döngü Koşulu",
        "prop_code": "Python Kodu",
        "prop_variables": "Başlangıç Değişkenleri",
        "prop_variable": "Değişken",
        "prop_prompt": "Soru (Prompt)",
        "prop_input_type": "Girdi Tipi",
        "prop_expression": "İfade",
        "prop_output_expression": "Çıktı İfadesi",
        "prop_counter": "Sayaç Değişkeni",
        "prop_start": "Başlangıç",
        "prop_end": "Bitiş (dahil değil)",
        "prop_step": "Artış (Step)",
        "prop_function_name": "Fonksiyon Adı",
        "prop_parameters": "Parametreler",
        "prop_return_expression": "Dönüş İfadesi",
        "prop_name": "Değişken Adı",
        "prop_value": "Başlangıç Değeri",
        "prop_type": "Tip (int/float/str/list/auto)",
        "prop_end_char": "Satır Sonu (\\n / '')",
        "prop_result": "Sonuç Değişkeni",
        "prop_operand_a": "Sol Taraf",
        "prop_operator": "Operatör",
        "prop_operand_b": "Sağ Taraf",
        "prop_operation": "İşlem",
        "prop_args": "Argümanlar",
        "prop_source": "Kaynak Değişken",
        "prop_target": "Hedef Tip",
        "prop_list_var": "Liste Değişkeni",
        "prop_condition_if": "If Koşulu",
        "prop_condition_elif": "Elif Koşulu",
        "prop_exception_type": "Hata Tipi",
        "prop_error_var": "Hata Değişkeni",
        "prop_cases": "Durumlar (virgülle)",
        "prop_message": "Mesaj",
        "prop_text": "Açıklama Metni",
        "prop_label": "Grup Adı",
        "prop_seconds": "Bekleme (saniye)",
        "prop_filepath": "Dosya Yolu",
        "prop_mode": "Mod",
        "prop_reverse": "Ters Sırala",
        "prop_key": "Anahtar (opsiyonel)",
        "prop_target_value": "Aranan Değer",
        "prop_var_a": "Birinci Değişken",
        "prop_var_b": "İkinci Değişken",
        "prop_accumulator": "Biriktirici",
        "prop_params": "Parametreler",
        "prop_body": "Gövde İfadesi",
        "prop_iterable": "İterable",
        "prop_loop_variable": "Döngü Değişkeni",
        "prop_condition_opt": "Koşul (opsiyonel)",
        "prop_module": "Modül Adı",
        "prop_alias": "Takma Ad",
        "prop_from_import": "from ... import",
        "prop_flow_tag": "Etiket (canvas alt satır)",
        "speed_label": "Hız:",
    },
    "en": {
        "cat_basic": "Basic",
        "cat_data": "Data & Variables",
        "cat_flow": "Flow Control",
        "cat_io": "I/O",
        "cat_algorithms": "Algorithms",
        "cat_functions": "Functions",
        "cat_advanced": "Advanced",
        "node_start": "Start",
        "node_process": "Process",
        "node_decision": "Decision",
        "node_stop": "Stop",
        "node_comment": "Comment",
        "node_variable": "Variable",
        "node_math": "Math",
        "node_string_operation": "String Operation",
        "node_type_cast": "Type Cast",
        "node_list_operation": "List Operation",
        "node_while": "While Loop",
        "node_for": "For Loop",
        "node_if_elif_else": "If / Elif / Else",
        "node_break": "Break",
        "node_continue": "Continue",
        "node_try_except": "Try / Except",
        "node_switch_match": "Switch / Match",
        "node_input": "Input",
        "node_output": "Output",
        "node_print": "Print",
        "node_file_read": "File Read",
        "node_file_write": "File Write",
        "node_random": "Random",
        "node_delay": "Delay",
        "node_sort": "Sort",
        "node_search": "Search",
        "node_swap": "Swap",
        "node_accumulate": "Accumulate",
        "node_function": "Function",
        "node_return": "Return",
        "node_lambda": "Lambda",
        "node_list_comprehension": "List Comprehension",
        "node_assert": "Assert",
        "node_import": "Import",
        "node_group": "Group",
        "dialog_edit_node": "Edit Node — {name}",
        "dialog_node_title": "📦  {name} Node",
        "dialog_properties": "Properties",
        "hint_double_click": "⚙ Double-click to edit…",
        "hint_start": "▶ Start",
        "hint_var_count": "{n} variables",
        "prop_description": "Description",
        "prop_condition": "Condition",
        "prop_loop_condition": "Loop Condition",
        "prop_code": "Python Code",
        "prop_variables": "Initial Variables",
        "prop_variable": "Variable",
        "prop_prompt": "Prompt",
        "prop_input_type": "Input Type",
        "prop_expression": "Expression",
        "prop_output_expression": "Output Expression",
        "prop_counter": "Counter Variable",
        "prop_start": "Start",
        "prop_end": "End (exclusive)",
        "prop_step": "Step",
        "prop_function_name": "Function Name",
        "prop_parameters": "Parameters",
        "prop_return_expression": "Return Expression",
        "prop_name": "Variable Name",
        "prop_value": "Initial Value",
        "prop_type": "Type (int/float/str/list/auto)",
        "prop_end_char": "Line End (\\n / '')",
        "prop_result": "Result Variable",
        "prop_operand_a": "Left Operand",
        "prop_operand_b": "Right Operand",
        "prop_operator": "Operator",
        "prop_operation": "Operation",
        "prop_args": "Arguments",
        "prop_source": "Source Variable",
        "prop_target": "Target Type",
        "prop_list_var": "List Variable",
        "prop_condition_if": "If Condition",
        "prop_condition_elif": "Elif Condition",
        "prop_exception_type": "Exception Type",
        "prop_error_var": "Error Variable",
        "prop_cases": "Cases (comma-separated)",
        "prop_message": "Message",
        "prop_text": "Comment Text",
        "prop_label": "Group Label",
        "prop_seconds": "Delay (seconds)",
        "prop_filepath": "File Path",
        "prop_mode": "Mode",
        "prop_reverse": "Reverse Sort",
        "prop_key": "Key (optional)",
        "prop_target_value": "Search Target",
        "prop_var_a": "First Variable",
        "prop_var_b": "Second Variable",
        "prop_accumulator": "Accumulator",
        "prop_params": "Parameters",
        "prop_body": "Body Expression",
        "prop_iterable": "Iterable",
        "prop_loop_variable": "Loop Variable",
        "prop_condition_opt": "Condition (optional)",
        "prop_module": "Module Name",
        "prop_alias": "Alias",
        "prop_from_import": "from ... import",
        "prop_flow_tag": "Tag (canvas subtitle)",
        "speed_label": "Speed:",
    },
}

# (property_key, i18n_label_key, default_value)
NODE_PROPERTY_SCHEMA: dict[str, list[tuple[str, str, str]]] = {
    "Variable": [
        ("name", "prop_name", "x"),
        ("value", "prop_value", "0"),
        ("type", "prop_type", "auto"),
    ],
    "Print": [
        ("expression", "prop_expression", ""),
        ("end", "prop_end_char", "\\n"),
    ],
    "Math": [
        ("result", "prop_result", "result"),
        ("operand_a", "prop_operand_a", "a"),
        ("operator", "prop_operator", "+"),
        ("operand_b", "prop_operand_b", "b"),
    ],
    "String Operation": [
        ("variable", "prop_variable", "s"),
        ("operation", "prop_operation", "upper"),
        ("args", "prop_args", ""),
        ("result", "prop_result", "result"),
    ],
    "Type Cast": [
        ("source", "prop_source", "x"),
        ("target", "prop_target", "int"),
        ("result", "prop_result", "result"),
    ],
    "List Operation": [
        ("list_var", "prop_list_var", "liste"),
        ("operation", "prop_operation", "append"),
        ("args", "prop_args", ""),
        ("result", "prop_result", ""),
    ],
    "If Elif Else": [
        ("condition_if", "prop_condition_if", "x > 0"),
        ("condition_elif", "prop_condition_elif", "x == 0"),
    ],
    "Break": [
        ("tag", "prop_flow_tag", ""),
        ("description", "prop_description", ""),
    ],
    "Continue": [
        ("tag", "prop_flow_tag", ""),
        ("description", "prop_description", ""),
    ],
    "Try Except": [
        ("exception_type", "prop_exception_type", "Exception"),
        ("error_var", "prop_error_var", "e"),
    ],
    "Switch Match": [
        ("variable", "prop_variable", "x"),
        ("cases", "prop_cases", "1,2,3,default"),
    ],
    "Stop": [("message", "prop_message", "")],
    "Comment": [("text", "prop_text", "")],
    "Group": [("label", "prop_label", "")],
    "Delay": [("seconds", "prop_seconds", "1")],
    "File Read": [
        ("filepath", "prop_filepath", "dosya.txt"),
        ("variable", "prop_variable", "icerik"),
        ("mode", "prop_mode", "all"),
    ],
    "File Write": [
        ("filepath", "prop_filepath", "cikti.txt"),
        ("expression", "prop_expression", ""),
        ("mode", "prop_mode", "w"),
    ],
    "Random": [
        ("operation", "prop_operation", "randint"),
        ("args", "prop_args", "1,100"),
        ("result", "prop_result", "r"),
    ],
    "Sort": [
        ("list_var", "prop_list_var", "liste"),
        ("reverse", "prop_reverse", "False"),
        ("key", "prop_key", ""),
    ],
    "Search": [
        ("list_var", "prop_list_var", "liste"),
        ("target", "prop_target_value", "hedef"),
        ("result", "prop_result", "index"),
    ],
    "Swap": [
        ("var_a", "prop_var_a", "a"),
        ("var_b", "prop_var_b", "b"),
    ],
    "Accumulate": [
        ("accumulator", "prop_accumulator", "toplam"),
        ("operation", "prop_operation", "+="),
        ("value", "prop_value", "x"),
    ],
    "Lambda": [
        ("name", "prop_name", "f"),
        ("params", "prop_params", "x"),
        ("body", "prop_body", "x * 2"),
    ],
    "List Comprehension": [
        ("result", "prop_result", "sonuc"),
        ("expression", "prop_expression", "x * 2"),
        ("variable", "prop_loop_variable", "x"),
        ("iterable", "prop_iterable", "liste"),
        ("condition", "prop_condition_opt", ""),
    ],
    "Assert": [
        ("condition", "prop_condition", "x > 0"),
        ("message", "prop_message", "Assertion failed"),
    ],
    "Import": [
        ("module", "prop_module", "math"),
        ("alias", "prop_alias", ""),
        ("from_import", "prop_from_import", ""),
    ],
    "Decision": [
        ("condition", "prop_condition", ""),
        ("description", "prop_description", ""),
    ],
    "While": [
        ("condition", "prop_loop_condition", ""),
        ("description", "prop_description", ""),
    ],
    "Process": [
        ("code", "prop_code", ""),
        ("description", "prop_description", ""),
    ],
    "Start": [("variables", "prop_variables", "")],
    "Input": [
        ("variable", "prop_variable", "USER_IN"),
        ("prompt", "prop_prompt", "Değer girin:"),
        ("input_type", "prop_input_type", "auto"),
    ],
    "Output": [("expression", "prop_output_expression", "")],
    "For": [
        ("variable", "prop_counter", "i"),
        ("start", "prop_start", "0"),
        ("end", "prop_end", "10"),
        ("step", "prop_step", "1"),
    ],
    "Function": [
        ("function_name", "prop_function_name", "my_func"),
        ("parameters", "prop_parameters", ""),
    ],
    "Return": [("expression", "prop_return_expression", "")],
}


def node_i18n_key(title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", title).strip("_").lower()
    return f"node_{slug}"


def tn(key: str, **kwargs) -> str:
    """Node-domain çeviri."""
    lang = current_language()
    table = NODE_STRINGS.get(lang, NODE_STRINGS["en"])
    text = table.get(key, NODE_STRINGS["en"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def t_node(title: str) -> str:
    return tn(node_i18n_key(title))


def t_cat(cat_key: str) -> str:
    return tn(cat_key)


def t_prop(label_key: str) -> str:
    return tn(label_key)


def all_node_titles() -> list[str]:
    seen: set[str] = set()
    titles: list[str] = []
    for nodes in NODE_CATEGORIES.values():
        for name in nodes:
            if name not in seen:
                seen.add(name)
                titles.append(name)
    return titles


_DISPLAY_TO_CANONICAL: dict[str, str] | None = None


def _build_display_to_canonical() -> dict[str, str]:
    global _DISPLAY_TO_CANONICAL
    if _DISPLAY_TO_CANONICAL is not None:
        return _DISPLAY_TO_CANONICAL
    mapping: dict[str, str] = {}
    for title in all_node_titles():
        mapping[title.lower()] = title
        for lang_table in NODE_STRINGS.values():
            label = lang_table.get(node_i18n_key(title), "")
            if label:
                mapping[label.strip().lower()] = title
    _DISPLAY_TO_CANONICAL = mapping
    return mapping


def resolve_canonical_node_title(raw: str) -> str:
    """Paletten gelen TR/EN görünen adı veya kısaltılmış metni kanonik İngilizce title'a çevirir."""
    text = (raw or "").strip()
    if not text:
        return raw
    for nodes in NODE_CATEGORIES.values():
        if text in nodes:
            return text
    mapping = _build_display_to_canonical()
    hit = mapping.get(text.lower())
    if hit:
        return hit
    # Eski sürükle-bırak: yalnızca son kelime gelmiş olabilir (ör. "İşlemi" ← "Metin İşlemi")
    last = text.rsplit(None, 1)[-1].lower()
    hit = mapping.get(last)
    if hit:
        return hit
    return text


_LEGACY_DEFAULT_PROPERTIES: dict[str, dict] = {
    "Start": {"variables": ""},
    "Process": {"code": "", "description": ""},
    "Decision": {"condition": "", "description": ""},
    "While": {"condition": "", "description": ""},
    "Input": {"variable": "USER_IN", "prompt": "Değer girin:", "input_type": "auto"},
    "Output": {"expression": ""},
    "For": {"variable": "i", "start": "0", "end": "10", "step": "1"},
    "Function": {"function_name": "my_func", "parameters": ""},
    "Return": {"expression": ""},
}


def default_properties_for(title: str) -> dict:
    """Şema + yerleşik varsayılanlardan başlangıç özellik sözlüğü."""
    props = dict(_LEGACY_DEFAULT_PROPERTIES.get(title, {}))
    for prop_key, _, default in NODE_PROPERTY_SCHEMA.get(title, []):
        props.setdefault(prop_key, default)
    return props
