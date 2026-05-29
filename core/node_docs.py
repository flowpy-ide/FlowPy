# core/node_docs.py
# ──────────────────────────────────────────────────────────────────────
# Düğüm tipi dokümantasyonu — hover tooltip içeriği.
# ──────────────────────────────────────────────────────────────────────

NODE_DOCS = {
    "Start": {
        "title": "Start — Başlangıç",
        "desc": "Her flow'un başlangıç noktası. Sadece bir tane olmalı.",
        "properties": {
            "variables": "Başlangıç değişkenlerini tanımla.\nÖrnek: x = 0\nsayac = 1",
        },
        "example": "# Üretilen kod:\ndef main():\n    # Flow başlıyor\n    pass",
        "tip": "Start node'u olmadan flow çalışmaz.",
    },
    "Process": {
        "title": "Process — İşlem",
        "desc": "Python kodu çalıştırır. Atama, hesaplama, liste işlemleri.",
        "properties": {
            "code": "Çalıştırılacak Python kodu.\nÖrnek: result = x * 2\nliste.append(x)",
        },
        "example": "result = x ** 2\ntoplam = a + b",
        "tip": "Birden fazla satır yazabilirsin.",
    },
    "Decision": {
        "title": "Decision — Karar",
        "desc": "Koşula göre True veya False yoluna dallanır.",
        "properties": {
            "condition": "Python bool ifadesi.\nÖrnek: x > 5\nx % 2 == 0",
        },
        "example": "Port 0 (True) → Koşul sağlandı\nPort 1 (False) → Koşul sağlanmadı",
        "tip": "Diamond şekli karar node'unu temsil eder.",
    },
    "Input": {
        "title": "Input — Kullanıcı Girişi",
        "desc": "Kullanıcıdan değer alır, değişkene atar.",
        "properties": {
            "variable": "Değişken adı",
            "prompt": "Kullanıcı mesajı",
            "input_type": "int / float / str / auto",
        },
        "example": "x = int(input('Sayı girin:'))",
        "tip": "input_type=int seçersen otomatik int() cast eklenir.",
    },
    "Output": {
        "title": "Output — Çıktı",
        "desc": "Ekrana değer yazdırır.",
        "properties": {
            "expression": "Yazdırılacak Python ifadesi.",
        },
        "example": "print(f'Sonuç: {result}')",
        "tip": "f-string kullanabilirsin.",
    },
    "While": {
        "title": "While — Koşullu Döngü",
        "desc": "Koşul True olduğu sürece döngü body'si çalışır.",
        "properties": {"condition": "Döngü devam koşulu."},
        "example": "Port 0 (Loop) → Döngü devam\nPort 1 (Exit) → Döngü bitti",
        "tip": "Sonsuz döngüye dikkat et.",
    },
    "For": {
        "title": "For — Sayaç Döngüsü",
        "desc": "Belirli aralıkta sayarak döner.",
        "properties": {
            "variable": "Sayaç",
            "start": "Başlangıç",
            "end": "Bitiş (dahil değil)",
            "step": "Adım",
        },
        "example": "for i in range(0, 10, 1):",
        "tip": "end değeri dahil değildir.",
    },
    "Function": {
        "title": "Function — Fonksiyon",
        "desc": "Yeniden kullanılabilir kod bloğu tanımlar.",
        "properties": {
            "function_name": "Fonksiyon adı",
            "parameters": "Parametreler",
        },
        "example": "def hesapla(x, y):",
        "tip": "Return node ile değer döndürebilirsin.",
    },
    "Return": {
        "title": "Return — Değer Döndür",
        "desc": "Fonksiyondan değer döndürür.",
        "properties": {"expression": "Döndürülecek ifade"},
        "example": "return x * 2",
        "tip": "Sadece Function içinde anlamlıdır.",
    },
}
