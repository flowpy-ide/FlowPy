"""Tam demo flowpy — dikey/kompakt yerleşim, geçerli port bağlantıları."""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "created_flows", "tam_demo.flowpy")


def nid(i: int) -> str:
    return f"a1000000-{i:04d}-4000-8000-000000000001"


nodes: list[dict] = []
edges: list[dict] = []


def node(i, title, x, y, props):
    nodes.append({
        "id": nid(i),
        "title": title,
        "x": float(x),
        "y": float(y),
        "properties": props,
    })


def edge(si, di, sp=0, dp=0):
    edges.append({
        "source_id": nid(si),
        "dest_id": nid(di),
        "source_port_index": sp,
        "dest_port_index": dp,
    })


# ── Düğümler (dikey ana hat x=0, döngü gövdeleri x=-280) ─────────────
node(1, "Start", 0, 0, {
    "variables": (
        "liste = []\n"
        "toplam = 0\n"
        "deneme = 0\n"
        "n = 5\n"
        "ortalama = 0\n"
        "mesaj = 'FlowPy tam demo'\n"
        "harf = 'F'\n"
        "skor = 0\n"
        "rapor = ''"
    ),
})

node(2, "Comment", -520, 0, {
    "text": "FlowPy Tam Demo — tüm düğüm tipleri.\nRun/Step ile çalıştırın.",
})

node(45, "Group", -520, 120, {
    "label": "Döngü & not üretimi",
})

node(3, "Import", 0, 100, {
    "module": "random",
    "alias": "",
    "from_import": "",
})

node(4, "While", 0, 220, {
    "condition": "deneme < 3",
    "description": "Geçerli n girilene kadar",
})

node(5, "Input", -280, 220, {
    "variable": "n",
    "prompt": "Kaç not? (1-10):",
    "input_type": "int",
})

node(6, "Decision", -280, 340, {
    "condition": "n > 0 and n <= 10",
    "description": "Geçerli aralık",
})

node(7, "Break", -280, 460, {
    "tag": "geçerli",
    "description": "While'dan çık (çıkış portu üzerinden)",
})

node(8, "Process", -280, 280, {
    "code": "deneme += 1",
    "description": "Hatalı giriş",
})

node(9, "Continue", -450, 310, {
    "tag": "tekrar",
    "description": "",
})

node(10, "Variable", 0, 380, {
    "name": "liste",
    "value": "[]",
    "type": "list",
    "description": "Not listesini sıfırla",
})

node(11, "For", 0, 500, {
    "variable": "i",
    "start": "0",
    "end": "n",
    "step": "1",
})

node(12, "Random", -280, 500, {
    "operation": "randint",
    "args": "40, 100",
    "result": "skor",
})

node(13, "Math", -280, 620, {
    "result": "skor",
    "operand_a": "skor",
    "operator": "+",
    "operand_b": "0",
})

node(14, "List Operation", -280, 740, {
    "list_var": "liste",
    "operation": "append",
    "args": "skor",
    "result": "",
})

node(15, "Accumulate", -280, 860, {
    "accumulator": "toplam",
    "operation": "+=",
    "value": "skor",
})

node(16, "Decision", -280, 980, {
    "condition": "skor >= 50",
    "description": "Geçer not",
})

node(17, "Continue", -450, 1010, {
    "tag": "düşük not",
    "description": "",
})

node(18, "Decision", -280, 1100, {
    "condition": "i >= n - 1",
    "description": "Son tur",
})

node(19, "Break", -280, 1220, {
    "tag": "for break",
    "description": "",
})

node(20, "Sort", 0, 640, {
    "list_var": "liste",
    "reverse": "False",
    "key": "",
})

node(21, "Search", 0, 760, {
    "list_var": "liste",
    "target": "75",
    "result": "indeks",
})

node(22, "Swap", 0, 880, {
    "var_a": "liste[0]",
    "var_b": "liste[1]",
    "description": "En az 2 eleman gerekir",
})

node(23, "Process", 0, 1000, {
    "code": "ortalama = (sum(liste) / len(liste)) if liste else (toplam / n if n else 0)",
    "description": "Ortalama",
})

node(24, "If Elif Else", 0, 1120, {
    "condition_if": "ortalama >= 85",
    "condition_elif": "ortalama >= 60",
})

node(25, "Process", 280, 1080, {
    "code": "mesaj = 'Mükemmel'; harf = 'A'",
    "description": "if",
})

node(26, "Process", 280, 1160, {
    "code": "mesaj = 'İyi'; harf = 'B'",
    "description": "elif",
})

node(27, "Process", 280, 1240, {
    "code": "mesaj = 'Geliştirilmeli'; harf = 'C'",
    "description": "else",
})

node(28, "Switch Match", 0, 1240, {
    "variable": "harf",
    "cases": "A,B,C,default",
})

node(29, "Try Except", 0, 1360, {
    "exception_type": "Exception",
    "error_var": "e",
})

node(30, "Process", -280, 1360, {
    "code": "guvenli = toplam / len(liste)",
    "description": "try",
})

node(31, "Print", -280, 1480, {
    "expression": "'Hata: ' + str(e)",
    "end": "\\n",
})

node(32, "String Operation", 0, 1480, {
    "variable": "mesaj",
    "operation": "upper",
    "args": "",
    "result": "mesaj",
})

node(33, "Type Cast", 0, 1600, {
    "source": "ortalama",
    "target": "int",
    "result": "ort_int",
})

node(34, "List Comprehension", 0, 1720, {
    "result": "kareler",
    "expression": "x * x",
    "variable": "x",
    "iterable": "liste",
    "condition": "x > 50",
})

node(35, "Lambda", 0, 1840, {
    "name": "iki_kat",
    "params": "x",
    "body": "x * 2",
})

node(36, "Function", 280, 1720, {
    "function_name": "puan_artir",
    "parameters": "x",
})

node(37, "Return", 280, 1840, {
    "expression": "x + 5",
})

node(38, "Assert", 0, 1960, {
    "condition": "ortalama >= 0",
    "message": "Ortalama negatif olamaz",
})

node(39, "Print", 0, 2080, {
    "expression": (
        "f'Ort={ortalama:.1f} harf={harf} liste={liste} kareler={kareler}'"
    ),
    "end": "\\n",
})

node(40, "Output", 0, 2200, {
    "expression": "f'indeks={indeks} ort_int={ort_int}'",
})

node(41, "File Write", 0, 2320, {
    "filepath": "created_flows/demo_rapor.txt",
    "expression": "f'Rapor: {mesaj} ort={ortalama}'",
    "mode": "w",
})

node(42, "File Read", 0, 2440, {
    "filepath": "created_flows/demo_rapor.txt",
    "variable": "rapor",
    "mode": "all",
})

node(43, "Delay", 0, 2560, {
    "seconds": "0.3",
})

node(44, "Stop", 0, 2680, {
    "message": "Tam demo bitti!",
})

# ── Kenarlar ─────────────────────────────────────────────────────────
edge(1, 3)
edge(3, 4)
edge(4, 5, 0)           # While loop → Input
edge(5, 6)
edge(6, 7, 0)           # geçerli → Break (yorumlayıcı While çıkışına gider)
edge(6, 8, 1)           # geçersiz → deneme++
edge(8, 9)
edge(9, 4, 0)           # Continue → While
edge(4, 10, 1)          # While çıkış → Variable (Break de buradan devam eder)
edge(10, 11)
edge(11, 12, 0)         # For döngü gövdesi
edge(12, 13)
edge(13, 14)
edge(14, 15)
edge(15, 16)
edge(16, 18, 0)         # yüksek not → son tur?
edge(16, 17, 1)         # düşük → Continue
edge(17, 11, 0)        # Continue → For
edge(18, 19, 0)        # son tur → Break
edge(18, 11, 1)        # değilse → For
edge(11, 20, 1)        # For çıkış → Sort
edge(20, 21)
edge(21, 22)
edge(22, 23)
edge(23, 24)
edge(24, 25, 0)
edge(24, 26, 1)
edge(24, 27, 2)
edge(25, 28)
edge(26, 28)
edge(27, 28)
for _sw_port in range(4):
    edge(28, 29, _sw_port)   # Switch tüm dallar → Try
edge(29, 30, 0)
edge(29, 31, 1)
edge(30, 32)
edge(31, 32)
edge(32, 33)
edge(33, 34)
edge(34, 35)
edge(35, 36)
edge(36, 37)
edge(37, 38)           # Return → Assert
edge(38, 39, 0)        # Assert geçti → Print
edge(39, 40)
edge(40, 41)
edge(41, 42)
edge(42, 43)
edge(43, 44)

data = {"nodes": nodes, "edges": edges}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Wrote {len(nodes)} nodes, {len(edges)} edges -> {OUT}")
print(f"Bounds approx: x=[-520,280] y=[0,2680]")
