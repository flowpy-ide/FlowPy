# core/interpreter.py
# ──────────────────────────────────────────────────────────────────────
# Interpreter : Sahnedeki düğüm akışını gerçekten çalıştıran motor.
#               Start → Process (exec) → Decision (eval → dallanma)
#               → While (döngü) düğümlerini yürütür.
#               Çalışan düğümü vurgulama (highlight) desteği.
# ──────────────────────────────────────────────────────────────────────

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QCoreApplication
from core.registry import NodeRegistry


class Interpreter(QObject):
    """Registry'deki düğümleri akış sırasıyla çalıştıran yorumlayıcı."""

    log_message = pyqtSignal(str)
    # Çalıştırma vurgulama sinyalleri
    highlight_node = pyqtSignal(object)       # düğümü vurgula
    clear_highlights = pyqtSignal()            # tüm vurguları temizle

    def __init__(self, registry: NodeRegistry, parent=None):
        super().__init__(parent)
        self.registry = registry
        self._scope: dict = {}

    # ══════════════════════════════════════════════════════════════════
    #  Ana Çalıştırma Döngüsü
    # ══════════════════════════════════════════════════════════════════

    def run_flow(self):
        """Start düğümünden başlayarak akışı adım adım yürütür."""
        self.clear_highlights.emit()
        nodes = self.registry.get_all_nodes()

        if not nodes:
            self.log_message.emit("⚠  Sahnede çalıştırılacak düğüm bulunamadı.")
            return

        start_node = None
        for node_id, node in nodes.items():
            if getattr(node, "title", "") == "Start":
                start_node = node
                break

        if not start_node:
            self.log_message.emit("⚠  Akışta bir 'Start' düğümü bulunamadı!")
            return

        self._scope = {}

        self.log_message.emit("═" * 50)
        self.log_message.emit("▶  Akış çalıştırılıyor…")
        self.log_message.emit("═" * 50)

        self._execute_node(start_node, step=1)

        self.log_message.emit("═" * 50)
        self.log_message.emit("✔  Akış tamamlandı.")
        self.log_message.emit(f"   Değişkenler: {self._scope}")
        self.log_message.emit("")

        # Kısa bir gecikme sonra vurguları temizle
        QTimer.singleShot(1500, self.clear_highlights.emit)

    # ══════════════════════════════════════════════════════════════════
    #  Düğüm Yürütme
    # ══════════════════════════════════════════════════════════════════

    def _execute_node(self, node, step: int = 1, max_steps: int = 500):
        """Verilen düğümü çalıştır, sonra bağlı bir sonraki düğüme geç."""
        if step > max_steps:
            self.log_message.emit("⚠  Maksimum adım sayısına ulaşıldı (sonsuz döngü?)")
            return step

        title = getattr(node, "title", "?")
        node_id = getattr(node, "node_id", "?")
        short_id = node_id[:8] if len(node_id) >= 8 else node_id

        # Düğümü vurgula
        self.highlight_node.emit(node)
        QCoreApplication.processEvents()  # UI güncellenmesini bekle

        # ── START ────────────────────────────────────────────────────
        if title == "Start":
            self.log_message.emit(f"  [{step}] ▶ START (ID: {short_id})")
            vars_code = node.properties.get("variables", "").strip()
            if vars_code:
                self.log_message.emit(f"       Değişkenler tanımlanıyor…")
                try:
                    exec(vars_code, {}, self._scope)
                    self.log_message.emit(f"       ✔ {self._scope}")
                except Exception as e:
                    self.log_message.emit(f"       ✗ Hata: {e}")

            next_node = self._get_next_node(node, port_index=0)
            if next_node:
                return self._execute_node(next_node, step + 1, max_steps)

        # ── PROCESS ──────────────────────────────────────────────────
        elif title == "Process":
            code = node.properties.get("code", "").strip()
            desc = node.properties.get("description", "")
            desc_str = f" ({desc})" if desc else ""
            self.log_message.emit(f"  [{step}] ⚙ PROCESS{desc_str} (ID: {short_id})")

            if code:
                self.log_message.emit(f"       Kod: {code.split(chr(10))[0]}…")
                try:
                    exec(code, {"__builtins__": __builtins__}, self._scope)
                    self.log_message.emit(f"       ✔ Çalıştırıldı → {self._scope}")
                except Exception as e:
                    self.log_message.emit(f"       ✗ Hata: {e}")
            else:
                self.log_message.emit(f"       (boş — kod tanımlanmamış)")

            next_node = self._get_next_node(node, port_index=0)
            if next_node:
                return self._execute_node(next_node, step + 1, max_steps)

        # ── DECISION ─────────────────────────────────────────────────
        elif title == "Decision":
            condition = node.properties.get("condition", "").strip()
            desc = node.properties.get("description", "")
            desc_str = f" ({desc})" if desc else ""
            self.log_message.emit(f"  [{step}] ❓ DECISION{desc_str} (ID: {short_id})")

            if not condition:
                self.log_message.emit(f"       ⚠ Koşul tanımlanmamış, atlanıyor…")
                return step

            try:
                result = eval(condition, {"__builtins__": __builtins__}, self._scope)
                result_bool = bool(result)
                self.log_message.emit(
                    f"       Koşul: {condition} → {'✓ True' if result_bool else '✗ False'}"
                )
            except Exception as e:
                self.log_message.emit(f"       ✗ Hata: {e}")
                return step

            port_index = 0 if result_bool else 1
            next_node = self._get_next_node(node, port_index=port_index)
            if next_node:
                return self._execute_node(next_node, step + 1, max_steps)
            else:
                branch = "True" if result_bool else "False"
                self.log_message.emit(f"       ({branch} dalında bağlı düğüm yok)")

        # ── WHILE ────────────────────────────────────────────────────
        elif title == "While":
            condition = node.properties.get("condition", "").strip()
            desc = node.properties.get("description", "")
            desc_str = f" ({desc})" if desc else ""
            self.log_message.emit(f"  [{step}] 🔁 WHILE{desc_str} (ID: {short_id})")

            if not condition:
                self.log_message.emit(f"       ⚠ Döngü koşulu tanımlanmamış, atlanıyor…")
                return step

            iteration = 0
            while step <= max_steps:
                # Koşulu değerlendir
                try:
                    result = eval(condition, {"__builtins__": __builtins__}, self._scope)
                    result_bool = bool(result)
                except Exception as e:
                    self.log_message.emit(f"       ✗ Koşul hatası: {e}")
                    return step

                if not result_bool:
                    # Koşul False → çıkış portuna git
                    self.log_message.emit(
                        f"       Döngü sona erdi (iterasyon: {iteration})"
                    )
                    exit_node = self._get_next_node(node, port_index=1)
                    if exit_node:
                        return self._execute_node(exit_node, step + 1, max_steps)
                    return step

                iteration += 1
                self.log_message.emit(
                    f"       İterasyon {iteration}: {condition} → ✓ True"
                )

                # Loop body portuna git (index 0)
                loop_body = self._get_next_node(node, port_index=0)
                if loop_body:
                    step = self._execute_node(loop_body, step + 1, max_steps)
                    if step is None:
                        step = max_steps + 1
                else:
                    self.log_message.emit(f"       (döngü gövdesi bağlı değil)")
                    break

                # Vurgula
                self.highlight_node.emit(node)
                QCoreApplication.processEvents()

            if step > max_steps:
                self.log_message.emit("⚠  Döngü: maksimum adım sayısı aşıldı!")

        else:
            self.log_message.emit(f"  [{step}] 📦 {title} (ID: {short_id})")
            next_node = self._get_next_node(node, port_index=0)
            if next_node:
                return self._execute_node(next_node, step + 1, max_steps)

        return step

    # ══════════════════════════════════════════════════════════════════
    #  Graf Takibi Yardımcıları
    # ══════════════════════════════════════════════════════════════════

    def _get_next_node(self, current_node, port_index: int = 0):
        """Belirtilen çıkış portundan bağlı olan sonraki düğümü döndürür."""
        if port_index >= len(current_node.output_ports):
            return None

        source_port = current_node.output_ports[port_index]

        for edge in current_node.edges:
            if getattr(edge, 'source_port', None) is source_port:
                return edge.dest_node

        return None
