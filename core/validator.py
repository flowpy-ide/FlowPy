# core/validator.py
# ──────────────────────────────────────────────────────────────────────
# FlowValidator: Çeşitli kurallar (Start düğümü, ulaşılabilirlik, vd.)
#                ile grafı yürütme (execution) öncesinde denetler.
# ──────────────────────────────────────────────────────────────────────

from core.registry import NodeRegistry

class ValidationError(Exception):
    def __init__(self, message, node=None):
        super().__init__(message)
        self.node = node

class FlowValidator:
    """Grafın (NodeRegistry) yürütülmeye uygun olup olmadığını kontrol eder."""

    def __init__(self, registry: NodeRegistry):
        self.registry = registry

    def validate(self) -> list[ValidationError]:
        """Tüm kontrolleri yapar ve varsa hata listesi döner."""
        errors = []
        nodes = self.registry.get_all_nodes()

        if not nodes:
            errors.append(ValidationError("Sahne boş, çalıştırılacak akış yok."))
            return errors

        # 1. Start düğümü kontrolü
        start_nodes = [n for n in nodes.values() if getattr(n, "title", "") == "Start"]
        if not start_nodes:
            errors.append(ValidationError("Akışta bir 'Start' düğümü olmalıdır!"))
            return errors
        if len(start_nodes) > 1:
            errors.append(ValidationError("Akışta birden fazla 'Start' düğümü olamaz!", start_nodes[1]))

        start_node = start_nodes[0]

        # 2. Ulaşılabilirlik (Reachability) Kontrolü (DFS)
        reachable = set()
        stack = [start_node]
        
        while stack:
            curr = stack.pop()
            if curr.node_id not in reachable:
                reachable.add(curr.node_id)
                # İleri doğru gidebileceği node'ları bul
                for edge in curr.edges:
                    # Sadece bu node'dan ÇIKAN edge'leri takip et
                    if hasattr(edge, 'source_node') and edge.source_node is curr:
                        stack.append(edge.dest_node)

        # Ulaşılmayan düğümleri tespit et
        for node_id, node in nodes.items():
            if node_id not in reachable:
                errors.append(ValidationError(f"'{node.title}' düğümüne Start düğümünden ulaşılamıyor. (Bağlantısız)", node))

        # 3. Decision düğümleri için boşta kalan (bağlanmayan) dal kontrolü
        for node in nodes.values():
            if getattr(node, "title", "") == "Decision":
                out_ports = node.output_ports
                has_true = False
                has_false = False
                
                for edge in node.edges:
                    if getattr(edge, 'source_node', None) is node:
                        if edge.source_port is out_ports[0]:
                            has_true = True
                        elif edge.source_port is out_ports[1]:
                            has_false = True
                
                if not has_true:
                    errors.append(ValidationError(f"Decision '{node.node_id[:5]}' düğümünün 'True' çıkışı boşta!", node))
                if not has_false:
                    errors.append(ValidationError(f"Decision '{node.node_id[:5]}' düğümünün 'False' çıkışı boşta!", node))

        return errors
