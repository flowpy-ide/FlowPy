# core/serializer.py
# ──────────────────────────────────────────────────────────────────────
# FlowSerializer : Akışı JSON olarak kaydet / yükle.
# ──────────────────────────────────────────────────────────────────────

import json
from core.registry import NodeRegistry
from models.node import BaseNode
from models.edge import Edge


class FlowSerializer:
    """Sahnedeki düğüm ve bağlantıları JSON'a serialize / deserialize eder."""

    @staticmethod
    def serialize_to_dict(registry: NodeRegistry) -> dict:
        """Kayıt defterini bir dictionary objesine dönüştürür."""
        data = {
            "nodes": [],
            "edges": []
        }

        # Düğümleri serialize et
        for node_id, node in registry.get_all_nodes().items():
            pos = node.pos()
            data["nodes"].append({
                "id": node_id,
                "title": node.title,
                "x": pos.x(),
                "y": pos.y(),
                "properties": node.properties.copy()
            })

        # Edge'leri serialize et
        for src_id, dst_id in registry.get_all_edges():
            src_node = registry.get_node(src_id)
            dst_node = registry.get_node(dst_id)
            src_port_idx = 0
            dst_port_idx = 0

            if src_node and dst_node:
                for edge in src_node.edges:
                    if hasattr(edge, 'dest_node') and edge.dest_node is dst_node:
                        for i, p in enumerate(src_node.output_ports):
                            if p is edge.source_port:
                                src_port_idx = i
                                break
                        for i, p in enumerate(dst_node.input_ports):
                            if p is edge.dest_port:
                                dst_port_idx = i
                                break
                        break

            data["edges"].append({
                "source_id": src_id,
                "dest_id": dst_id,
                "source_port_index": src_port_idx,
                "dest_port_index": dst_port_idx
            })

        return data

    @staticmethod
    def save_to_file(filepath: str, registry: NodeRegistry, scene):
        """Akışı JSON dosyasına kaydeder."""
        data = FlowSerializer.serialize_to_dict(registry)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return len(data["nodes"]), len(data["edges"])

    @staticmethod
    def deserialize_from_dict(data: dict, registry: NodeRegistry, scene):
        """Dictionary objesinden sahneyi geri yükler."""
        scene.clear()
        registry.clear()
        node_map = {}

        for node_data in data.get("nodes", []):
            node = BaseNode(title=node_data["title"])
            node.node_id = node_data["id"]
            node.properties = node_data.get("properties", {})

            registry.nodes[node.node_id] = node
            scene.addItem(node)
            node.setPos(node_data["x"], node_data["y"])
            node_map[node_data["id"]] = node

        for edge_data in data.get("edges", []):
            src_id = edge_data["source_id"]
            dst_id = edge_data["dest_id"]
            src_port_idx = edge_data.get("source_port_index", 0)
            dst_port_idx = edge_data.get("dest_port_index", 0)

            src_node = node_map.get(src_id)
            dst_node = node_map.get(dst_id)

            if src_node and dst_node:
                src_port = src_node.output_ports[src_port_idx] \
                    if src_port_idx < len(src_node.output_ports) else None
                dst_port = dst_node.input_ports[dst_port_idx] \
                    if dst_port_idx < len(dst_node.input_ports) else None

                if src_port and dst_port:
                    edge = Edge(src_node, dst_node,
                                source_port=src_port,
                                dest_port=dst_port)
                    scene.addItem(edge)
                    registry.add_edge(src_id, dst_id)

        return len(data.get("nodes", [])), len(data.get("edges", []))

    @staticmethod
    def load_from_file(filepath: str, registry: NodeRegistry, scene):
        """JSON dosyasından akışı yükler."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        return FlowSerializer.deserialize_from_dict(data, registry, scene)
