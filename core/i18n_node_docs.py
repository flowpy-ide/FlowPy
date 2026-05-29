# core/i18n_node_docs.py — Düğüm hover tooltip metinleri (TR / EN)

from core.i18n import current_language
from core.i18n_nodes import resolve_canonical_node_title

_DOCS_TR = {
    "Start": {
        "title": "Start — Başlangıç",
        "desc": "Her akışın başlangıç noktası. Yalnızca bir tane olmalı.",
        "example": "def main():\n    # akış başlar",
        "tip": "Start olmadan akış çalışmaz.",
    },
    "Process": {
        "title": "Process — İşlem",
        "desc": "Python kodu çalıştırır.",
        "example": "result = x * 2",
        "tip": "Birden fazla satır yazabilirsin.",
    },
    "Decision": {
        "title": "Decision — Karar",
        "desc": "Koşula göre True veya False dalına gider.",
        "example": "Port 0 → True\nPort 1 → False",
        "tip": "Baklava şekli karar düğümünü gösterir.",
    },
    "Stop": {
        "title": "Stop — Durdur",
        "desc": "Akışı sonlandırır.",
        "example": "return",
        "tip": "Sonrasındaki düğümler çalışmaz.",
    },
    "Comment": {
        "title": "Comment — Yorum",
        "desc": "Çalışma zamanında atlanır; kodda yorum olarak üretilir.",
        "example": "# açıklama",
        "tip": "Bağlantı portu yoktur.",
    },
    "Variable": {
        "title": "Variable — Değişken",
        "desc": "Değişken tanımlar veya değer atar.",
        "example": "x = 0",
        "tip": "value alanına ifade yazılabilir.",
    },
    "Math": {
        "title": "Math — Matematik",
        "desc": "İki operand üzerinde işlem yapar.",
        "example": "toplam = a + b",
        "tip": "Operatör: + - * / // % **",
    },
    "String Operation": {
        "title": "String Operation",
        "desc": "Metin üzerinde upper, split, replace vb.",
        "example": "s.upper()",
        "tip": "args alanını işleme göre doldur.",
    },
    "Type Cast": {
        "title": "Type Cast",
        "desc": "Değeri başka tipe çevirir.",
        "example": "int(x)",
        "tip": "Geçersiz dönüşüm hata verir.",
    },
    "List Operation": {
        "title": "List Operation",
        "desc": "Liste üzerinde append, sort, len vb.",
        "example": "liste.append(5)",
        "tip": "sort/reverse yerinde çalışır.",
    },
    "While": {
        "title": "While — Döngü",
        "desc": "Koşul doğru olduğu sürece tekrarlar.",
        "example": "Port 0 → Loop\nPort 1 → Exit",
        "tip": "Sonsuz döngüye dikkat.",
    },
    "For": {
        "title": "For — Sayaç",
        "desc": "Belirli aralıkta sayar.",
        "example": "for i in range(0, 10, 1)",
        "tip": "end dahil değildir.",
    },
    "If Elif Else": {
        "title": "If / Elif / Else",
        "desc": "Üç çıkış: if, elif, else.",
        "example": "if / elif / else dalları",
        "tip": "Hiçbiri tutmazsa else portu.",
    },
    "Break": {
        "title": "Break",
        "desc": "Döngüden çıkar.",
        "example": "break",
        "tip": "While/For gövdesinde kullan.",
    },
    "Continue": {
        "title": "Continue",
        "desc": "Sonraki tura atlar.",
        "example": "continue",
        "tip": "While/For gövdesinde kullan.",
    },
    "Try Except": {
        "title": "Try / Except",
        "desc": "Hata yakalama dalları.",
        "example": "try / except portları",
        "tip": "Port 0 try, Port 1 except.",
    },
    "Switch Match": {
        "title": "Switch / Match",
        "desc": "Değere göre case portları.",
        "example": "match x: case ...",
        "tip": "cases değişince port sayısı güncellenir.",
    },
    "Input": {
        "title": "Input — Girdi",
        "desc": "Kullanıcıdan değer alır.",
        "example": "x = int(input('...'))",
        "tip": "input_type ile cast.",
    },
    "Output": {
        "title": "Output — Çıktı",
        "desc": "Ekrana yazar.",
        "example": "print(expr)",
        "tip": "f-string kullanılabilir.",
    },
    "Print": {
        "title": "Print",
        "desc": "print benzeri çıktı.",
        "example": "print(x, end='')",
        "tip": "end parametresi ayarlanabilir.",
    },
    "File Read": {
        "title": "File Read",
        "desc": "Dosyadan okur.",
        "example": "with open(...) as f",
        "tip": "mode: all / lines / line",
    },
    "File Write": {
        "title": "File Write",
        "desc": "Dosyaya yazar.",
        "example": "f.write(...)",
        "tip": "w üzerine, a ekleme.",
    },
    "Random": {
        "title": "Random",
        "desc": "Rastgele değer üretir.",
        "example": "random.randint(1,100)",
        "tip": "args: 1,100 formatı.",
    },
    "Delay": {
        "title": "Delay",
        "desc": "Belirtilen süre bekler.",
        "example": "time.sleep(1)",
        "tip": "Adım adım izleme için.",
    },
    "Sort": {
        "title": "Sort",
        "desc": "Listeyi sıralar.",
        "example": "liste.sort()",
        "tip": "reverse=True ters sıra.",
    },
    "Search": {
        "title": "Search",
        "desc": "Listede arar.",
        "example": "bulundu / bulunamadı",
        "tip": "index -1 ise yok.",
    },
    "Swap": {
        "title": "Swap",
        "desc": "İki değişkeni takas eder.",
        "example": "a, b = b, a",
        "tip": "Sıralama algoritmalarında.",
    },
    "Accumulate": {
        "title": "Accumulate",
        "desc": "Biriktirici +=, *= vb.",
        "example": "toplam += x",
        "tip": "Döngü içinde kullanışlı.",
    },
    "Function": {
        "title": "Function",
        "desc": "Fonksiyon tanımı.",
        "example": "def f(a, b):",
        "tip": "Return ile dönüş.",
    },
    "Return": {
        "title": "Return",
        "desc": "Değer döndürür.",
        "example": "return x",
        "tip": "Fonksiyon akışında.",
    },
    "Lambda": {
        "title": "Lambda",
        "desc": "Tek satırlık fonksiyon.",
        "example": "f = lambda x: x*2",
        "tip": "body tek ifade olmalı.",
    },
    "List Comprehension": {
        "title": "List Comprehension",
        "desc": "Liste üretim ifadesi.",
        "example": "[x*2 for x in liste]",
        "tip": "condition opsiyonel.",
    },
    "Assert": {
        "title": "Assert",
        "desc": "Koşul doğrulama.",
        "example": "geçti / başarısız portları",
        "tip": "Test için.",
    },
    "Import": {
        "title": "Import",
        "desc": "Modül yükler.",
        "example": "import math",
        "tip": "from_import öncelikli.",
    },
    "Group": {
        "title": "Group",
        "desc": "Görsel gruplama.",
        "example": "(kapsayıcı)",
        "tip": "Port yok.",
    },
}

_DOCS_EN = {
    "Start": {
        "title": "Start",
        "desc": "Entry point of every flow. Only one allowed.",
        "example": "def main():\n    # flow starts",
        "tip": "Flow cannot run without Start.",
    },
    "Process": {
        "title": "Process",
        "desc": "Executes Python code.",
        "example": "result = x * 2",
        "tip": "Multiple lines supported.",
    },
    "Decision": {
        "title": "Decision",
        "desc": "Branches on True or False.",
        "example": "Port 0 → True\nPort 1 → False",
        "tip": "Diamond shape indicates branch.",
    },
    "Stop": {
        "title": "Stop",
        "desc": "Terminates the flow.",
        "example": "return",
        "tip": "Nodes after Stop do not run.",
    },
    "Comment": {
        "title": "Comment",
        "desc": "Skipped at runtime; emitted as code comment.",
        "example": "# note",
        "tip": "No connection ports.",
    },
    "Variable": {
        "title": "Variable",
        "desc": "Defines or assigns a variable.",
        "example": "x = 0",
        "tip": "value can be an expression.",
    },
    "Math": {
        "title": "Math",
        "desc": "Arithmetic on two operands.",
        "example": "sum = a + b",
        "tip": "Operators: + - * / // % **",
    },
    "String Operation": {
        "title": "String Operation",
        "desc": "String ops: upper, split, replace, etc.",
        "example": "s.upper()",
        "tip": "Fill args when needed.",
    },
    "Type Cast": {
        "title": "Type Cast",
        "desc": "Casts value to another type.",
        "example": "int(x)",
        "tip": "Invalid cast raises error.",
    },
    "List Operation": {
        "title": "List Operation",
        "desc": "List ops: append, sort, len, etc.",
        "example": "lst.append(5)",
        "tip": "sort/reverse are in-place.",
    },
    "While": {
        "title": "While Loop",
        "desc": "Repeats while condition is true.",
        "example": "Port 0 → Loop\nPort 1 → Exit",
        "tip": "Watch for infinite loops.",
    },
    "For": {
        "title": "For Loop",
        "desc": "Counter loop over a range.",
        "example": "for i in range(0, 10, 1)",
        "tip": "end is exclusive.",
    },
    "If Elif Else": {
        "title": "If / Elif / Else",
        "desc": "Three branches: if, elif, else.",
        "example": "if / elif / else paths",
        "tip": "Uses else port when no match.",
    },
    "Break": {
        "title": "Break",
        "desc": "Exits the current loop.",
        "example": "break",
        "tip": "Use inside While/For body.",
    },
    "Continue": {
        "title": "Continue",
        "desc": "Skips to next iteration.",
        "example": "continue",
        "tip": "Use inside While/For body.",
    },
    "Try Except": {
        "title": "Try / Except",
        "desc": "Error handling branches.",
        "example": "try / except ports",
        "tip": "Port 0 try, Port 1 except.",
    },
    "Switch Match": {
        "title": "Switch / Match",
        "desc": "Routes by matched value.",
        "example": "match x: case ...",
        "tip": "Port count follows cases list.",
    },
    "Input": {
        "title": "Input",
        "desc": "Reads user input.",
        "example": "x = int(input('...'))",
        "tip": "Cast via input_type.",
    },
    "Output": {
        "title": "Output",
        "desc": "Prints to console.",
        "example": "print(expr)",
        "tip": "f-strings work.",
    },
    "Print": {
        "title": "Print",
        "desc": "Print-like output.",
        "example": "print(x, end='')",
        "tip": "end parameter supported.",
    },
    "File Read": {
        "title": "File Read",
        "desc": "Reads from a file.",
        "example": "with open(...) as f",
        "tip": "mode: all / lines / line",
    },
    "File Write": {
        "title": "File Write",
        "desc": "Writes to a file.",
        "example": "f.write(...)",
        "tip": "w overwrite, a append.",
    },
    "Random": {
        "title": "Random",
        "desc": "Random value generation.",
        "example": "random.randint(1,100)",
        "tip": "args like 1,100 for randint.",
    },
    "Delay": {
        "title": "Delay",
        "desc": "Pauses for given seconds.",
        "example": "time.sleep(1)",
        "tip": "Useful for stepped runs.",
    },
    "Sort": {
        "title": "Sort",
        "desc": "Sorts a list.",
        "example": "lst.sort()",
        "tip": "reverse=True for descending.",
    },
    "Search": {
        "title": "Search",
        "desc": "Searches in a list.",
        "example": "found / not found ports",
        "tip": "index -1 means not found.",
    },
    "Swap": {
        "title": "Swap",
        "desc": "Swaps two variables.",
        "example": "a, b = b, a",
        "tip": "Common in sorting.",
    },
    "Accumulate": {
        "title": "Accumulate",
        "desc": "Applies +=, *=, etc.",
        "example": "total += x",
        "tip": "Ideal inside loops.",
    },
    "Function": {
        "title": "Function",
        "desc": "Defines a function block.",
        "example": "def f(a, b):",
        "tip": "Use Return to return.",
    },
    "Return": {
        "title": "Return",
        "desc": "Returns a value.",
        "example": "return x",
        "tip": "Within function flow.",
    },
    "Lambda": {
        "title": "Lambda",
        "desc": "Inline lambda function.",
        "example": "f = lambda x: x*2",
        "tip": "body must be one expression.",
    },
    "List Comprehension": {
        "title": "List Comprehension",
        "desc": "Builds a list via comprehension.",
        "example": "[x*2 for x in lst]",
        "tip": "condition is optional.",
    },
    "Assert": {
        "title": "Assert",
        "desc": "Validates a condition.",
        "example": "pass / fail ports",
        "tip": "For testing.",
    },
    "Import": {
        "title": "Import",
        "desc": "Imports a module.",
        "example": "import math",
        "tip": "from_import takes priority.",
    },
    "Group": {
        "title": "Group",
        "desc": "Visual grouping only.",
        "example": "(container)",
        "tip": "No ports.",
    },
}

NODE_DOCS_BY_LANG = {"tr": _DOCS_TR, "en": _DOCS_EN}


def get_node_doc(title: str) -> dict | None:
    canonical = resolve_canonical_node_title(title)
    lang = current_language()
    table = NODE_DOCS_BY_LANG.get(lang, _DOCS_EN)
    return table.get(canonical) or NODE_DOCS_BY_LANG["en"].get(canonical)
