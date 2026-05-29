# core/templates.py
# ──────────────────────────────────────────────────────────────────────
# Hazır flow şablonları ve yükleme yardımcıları.
# ──────────────────────────────────────────────────────────────────────

from models.node import BaseNode
from models.edge import Edge


TEMPLATES = {
    "Merhaba Dünya": {
        "description": "İlk flow — kullanıcıdan isim al, ekrana yaz",
        "category": "Başlangıç",
        "nodes": [
            {"id": "n1", "title": "Start", "x": -200, "y": 0, "properties": {}},
            {"id": "n2", "title": "Input", "x": 0, "y": 0,
             "properties": {"variable": "isim", "prompt": "Adını gir:"}},
            {"id": "n3", "title": "Output", "x": 200, "y": 0,
             "properties": {"expression": "f'Merhaba, {isim}!'"}},
        ],
        "edges": [("n1", "n2"), ("n2", "n3")],
    },
    "Faktöriyel": {
        "description": "Döngü ile n! hesapla",
        "category": "Döngüler",
        "nodes": [
            {"id": "n1", "title": "Start", "x": -300, "y": 0,
             "properties": {"variables": "sonuc = 1"}},
            {"id": "n2", "title": "Input", "x": -100, "y": 0,
             "properties": {"variable": "n", "prompt": "n girin (pozitif tam sayı):"}},
            {"id": "n3", "title": "For", "x": 100, "y": 0,
             "properties": {"variable": "i", "start": "1", "end": "n+1", "step": "1"}},
            {"id": "n4", "title": "Process", "x": 100, "y": 150,
             "properties": {"code": "sonuc = sonuc * i"}},
            {"id": "n5", "title": "Output", "x": 300, "y": 0,
             "properties": {"expression": "f'{n}! = {sonuc}'"}},
        ],
        "edges": [
            ("n1", "n2"), ("n2", "n3"), ("n3", "n4", "loop"),
            ("n4", "n3"), ("n3", "n5", "exit"),
        ],
    },
    "Sayı Tahmin": {
        "description": "Kullanıcı doğru sayıyı bulana kadar döngü",
        "category": "Koşullar",
        "nodes": [
            {"id": "n1", "title": "Start", "x": -300, "y": 0,
             "properties": {"variables": "gizli = 42\ndeneme = 0"}},
            {"id": "n2", "title": "While", "x": -100, "y": 0,
             "properties": {"condition": "True"}},
            {"id": "n3", "title": "Input", "x": -100, "y": 150,
             "properties": {"variable": "tahmin", "prompt": "Sayıyı tahmin et (1-100):"}},
            {"id": "n4", "title": "Process", "x": 100, "y": 150,
             "properties": {"code": "deneme += 1"}},
            {"id": "n5", "title": "Decision", "x": 300, "y": 150,
             "properties": {"condition": "tahmin == gizli"}},
            {"id": "n6", "title": "Output", "x": 300, "y": 0,
             "properties": {"expression": "f'Doğru! {deneme} denemede buldun.'"}},
            {"id": "n7", "title": "Output", "x": 500, "y": 150,
             "properties": {"expression": "'Küçük' if tahmin < gizli else 'Büyük'"}},
        ],
        "edges": [
            ("n1", "n2"), ("n2", "n3", "loop"), ("n3", "n4"), ("n4", "n5"),
            ("n5", "n6", "true"), ("n5", "n7", "false"), ("n7", "n2"),
        ],
    },
    "Bubble Sort": {
        "description": "Kabarcık sıralaması görsel olarak",
        "category": "Algoritmalar",
        "nodes": [
            {"id": "n1", "title": "Start", "x": -200, "y": 0,
             "properties": {"variables": "liste = [64, 34, 25, 12, 22, 11, 90]\nn = len(liste)"}},
            {"id": "n2", "title": "For", "x": 0, "y": 0,
             "properties": {"variable": "i", "start": "0", "end": "n-1", "step": "1"}},
            {"id": "n3", "title": "For", "x": 0, "y": 150,
             "properties": {"variable": "j", "start": "0", "end": "n-i-1", "step": "1"}},
            {"id": "n4", "title": "Decision", "x": 200, "y": 150,
             "properties": {"condition": "liste[j] > liste[j+1]"}},
            {"id": "n5", "title": "Process", "x": 200, "y": 300,
             "properties": {"code": "liste[j], liste[j+1] = liste[j+1], liste[j]"}},
            {"id": "n6", "title": "Output", "x": 400, "y": 0,
             "properties": {"expression": "f'Sıralı: {liste}'"}},
        ],
        "edges": [
            ("n1", "n2"), ("n2", "n3", "loop"), ("n3", "n4", "loop"),
            ("n4", "n5", "true"), ("n5", "n3"), ("n4", "n3", "false"),
            ("n3", "n2", "exit"), ("n2", "n6", "exit"),
        ],
    },
    "FizzBuzz": {
        "description": "Klasik FizzBuzz — 1'den 20'ye",
        "category": "Başlangıç",
        "nodes": [
            {"id": "n1", "title": "Start", "x": -200, "y": 0, "properties": {}},
            {"id": "n2", "title": "For", "x": 0, "y": 0,
             "properties": {"variable": "i", "start": "1", "end": "21", "step": "1"}},
            {"id": "n3", "title": "Decision", "x": 200, "y": 0,
             "properties": {"condition": "i % 15 == 0"}},
            {"id": "n4", "title": "Output", "x": 400, "y": -50,
             "properties": {"expression": "'FizzBuzz'"}},
            {"id": "n5", "title": "Decision", "x": 400, "y": 50,
             "properties": {"condition": "i % 3 == 0"}},
            {"id": "n6", "title": "Output", "x": 600, "y": 0,
             "properties": {"expression": "'Fizz'"}},
            {"id": "n7", "title": "Decision", "x": 600, "y": 100,
             "properties": {"condition": "i % 5 == 0"}},
            {"id": "n8", "title": "Output", "x": 800, "y": 50,
             "properties": {"expression": "'Buzz'"}},
            {"id": "n9", "title": "Output", "x": 800, "y": 150,
             "properties": {"expression": "i"}},
        ],
        "edges": [
            ("n1", "n2"), ("n2", "n3", "loop"), ("n3", "n4", "true"),
            ("n3", "n5", "false"), ("n5", "n6", "true"), ("n5", "n7", "false"),
            ("n7", "n8", "true"), ("n7", "n9", "false"),
        ],
    },
}


def _port_index_for_edge(src_node: BaseNode, branch: str | None) -> int:
    if not branch or branch in ("loop", "true"):
        return 0
    if branch in ("false", "exit"):
        return 1 if len(src_node.output_ports) > 1 else 0
    return 0


def load_template(name: str, registry, scene) -> bool:
    """Şablonu registry ve sahneye yükler."""
    template = TEMPLATES.get(name)
    if not template:
        return False

    registry.clear()
    scene.clear()
    node_map = {}

    for node_def in template["nodes"]:
        node = BaseNode(title=node_def["title"])
        node.properties.update(node_def.get("properties", {}))
        node_id = registry.add_node(node)
        node.node_id = node_id
        node_map[node_def["id"]] = node
        scene.addItem(node)
        node.setPos(node_def["x"], node_def["y"])

    for edge_def in template["edges"]:
        src_key, dst_key = edge_def[0], edge_def[1]
        branch = edge_def[2] if len(edge_def) > 2 else None
        src_id = node_map.get(src_key)
        dst_id = node_map.get(dst_key)
        if not src_id or not dst_id:
            continue
        src_node = registry.get_node(src_id)
        dst_node = registry.get_node(dst_id)
        if not src_node or not dst_node:
            continue
        if not src_node.output_ports or not dst_node.input_ports:
            continue
        port_idx = _port_index_for_edge(src_node, branch)
        src_port = src_node.output_ports[
            min(port_idx, len(src_node.output_ports) - 1)
        ]
        dst_port = dst_node.input_ports[0]
        edge = Edge(src_node, dst_node, source_port=src_port, dest_port=dst_port)
        scene.addItem(edge)
        registry.add_edge(src_id, dst_id)

    scene.history_changed.emit()
    return True
