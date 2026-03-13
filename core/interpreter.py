# core/interpreter.py
# ──────────────────────────────────────────────────────────────────────
# Interpreter : Sahnedeki düğüm akışını okuyan temel çalıştırma motoru.
#               Şimdilik mock log mesajları üretir; ileride AST
#               tabanlı gerçek yürütme burada gerçekleşecek.
# ──────────────────────────────────────────────────────────────────────

from PyQt6.QtCore import QObject, pyqtSignal
from core.registry import NodeRegistry


class Interpreter(QObject):
    """Registry'deki düğümleri tarayıp çalıştırma döngüsü yürüten yorumlayıcı."""

    # Ana penceredeki consoleOutput'a bağlanacak sinyal
    log_message = pyqtSignal(str)

    def __init__(self, registry: NodeRegistry, parent=None):
        super().__init__(parent)
        self.registry = registry

    # ── Execution Loop ───────────────────────────────────────────────

    def run_flow(self):
        """Registry'deki tüm düğümleri sırayla tarar ve mock log üretir."""
        nodes = self.registry.get_all_nodes()

        if not nodes:
            self.log_message.emit("⚠  Sahnede çalıştırılacak düğüm bulunamadı.")
            return

        self.log_message.emit("═" * 50)
        self.log_message.emit("▶  Akış çalıştırılıyor…")
        self.log_message.emit("═" * 50)

        step = 1
        for node_id, node in nodes.items():
            node_title = getattr(node, "title", "Bilinmeyen")
            msg = (f"  [{step}] Çalıştırılan Düğüm: {node_title}  "
                   f"(ID: {node_id[:8]}…)")
            self.log_message.emit(msg)
            step += 1

        # Edge bilgilerini de logla
        edges = self.registry.get_all_edges()
        if edges:
            self.log_message.emit("─" * 50)
            self.log_message.emit("  Bağlantılar:")
            for src, dst in edges:
                self.log_message.emit(f"    {src[:8]} → {dst[:8]}")

        self.log_message.emit("═" * 50)
        self.log_message.emit(f"✔  Toplam {step - 1} düğüm işlendi.")
        self.log_message.emit("")
