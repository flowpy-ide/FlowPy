# core/interpreter.py
# ──────────────────────────────────────────────────────────────────────
# Interpreter : Sahnedeki düğüm akışını adımlı (State Machine) olarak
#               çalıştıran motor.
# ──────────────────────────────────────────────────────────────────────

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QCoreApplication
from core.registry import NodeRegistry

class Interpreter(QObject):
    """Registry'deki düğümleri state machine yapısıyla çalıştıran yorumlayıcı."""

    log_message = pyqtSignal(str)
    highlight_node = pyqtSignal(object)       
    clear_highlights = pyqtSignal()           
    
    # Yeni sinyaller: Debugger ve Watcher için
    scope_changed = pyqtSignal(dict)
    flow_state_changed = pyqtSignal(bool, bool)  # (is_active, is_paused)

    def __init__(self, registry: NodeRegistry, parent=None):
        super().__init__(parent)
        self.registry = registry
        self._scope: dict = {}
        
        # State Machine Değişkenleri
        self._current_node = None
        self._current_step = 0
        self._is_active = False
        self._is_paused = False
        self.MAX_STEPS = 500

    # ══════════════════════════════════════════════════════════════════
    #  Kontrolcüler (Run / Step / Stop)
    # ══════════════════════════════════════════════════════════════════

    def run_flow(self):
        """Akışı başlatır ve (eğer duraklatılmışsa) kesintisiz devam ettirir."""
        if not self._is_active:
            if not self._init_flow():
                return
                
        self._is_paused = False
        self.flow_state_changed.emit(True, False)
        self.log_message.emit("▶  Akış yürütülüyor…")
        
        # Tamamlanana veya duraklatılana kadar çalış
        while self._current_node and not self._is_paused:
            self._process_current_node()
            QCoreApplication.processEvents()

    def step_flow(self):
        """Akışı sadece bir düğüm işleyecek şekilde ilerletir."""
        if not self._is_active:
            if not self._init_flow():
                return
                
        self._is_paused = True
        self.flow_state_changed.emit(True, True)
        self._process_current_node()

    def stop_flow(self):
        """Çalıştırılan akışı tamamen iptal eder."""
        if not self._is_active:
            return
            
        self._is_active = False
        self._is_paused = False
        self._current_node = None
        self.flow_state_changed.emit(False, False)
        self.clear_highlights.emit()
        self.log_message.emit("⏹ Çalıştırma durduruldu.")

    # ══════════════════════════════════════════════════════════════════
    #  İç Mantık
    # ══════════════════════════════════════════════════════════════════

    def _init_flow(self) -> bool:
        """Sahnede Start düğümünü bulur ve state'i sıfırlar."""
        self.clear_highlights.emit()
        nodes = self.registry.get_all_nodes()

        if not nodes:
            self.log_message.emit("⚠  Sahnede çalıştırılacak düğüm bulunamadı.")
            return False

        start_node = None
        for node_id, node in nodes.items():
            if getattr(node, "title", "") == "Start":
                start_node = node
                break

        if not start_node:
            self.log_message.emit("⚠  Akışta bir 'Start' düğümü bulunamadı!")
            return False

        self._scope = {}
        self.scope_changed.emit(self._scope)
        self._current_step = 1
        self._current_node = start_node
        self._is_active = True
        
        self.log_message.emit("═" * 50)
        self.log_message.emit("🔄 Oturum Başladı")
        self.log_message.emit("═" * 50)
        
        # İlk düğümü vurgula
        self.highlight_node.emit(self._current_node)
        return True

    def _finish_flow(self):
        """Akış başarıyla bittiğinde çağrılır."""
        self.log_message.emit("═" * 50)
        self.log_message.emit("✔  Akış tamamlandı.")
        self.log_message.emit(f"   Sonuç Değişkenler: {self._scope}")
        self.log_message.emit("")
        
        self._is_active = False
        self._is_paused = False
        self._current_node = None
        self.flow_state_changed.emit(False, False)
        QTimer.singleShot(1500, self.clear_highlights.emit)

    def _process_current_node(self):
        """Sıradaki tek düğümü çalıştırır ve state'i günceller."""
        if not self._current_node:
            self._finish_flow()
            return
            
        if self._current_step > self.MAX_STEPS:
            self.log_message.emit("⚠  Maksimum adım sayısına ulaşıldı (sonsuz döngü?)")
            self.stop_flow()
            return

        node = self._current_node
        step = self._current_step
        
        title = getattr(node, "title", "?")
        node_id = getattr(node, "node_id", "?")
        short_id = node_id[:8] if len(node_id) >= 8 else node_id

        # Düğümü vurgula
        self.highlight_node.emit(node)
        
        next_node = None
        
        # ── START ────────────────────────────────────────────────────
        if title == "Start":
            self.log_message.emit(f"  [{step}] ▶ START (ID: {short_id})")
            vars_code = node.properties.get("variables", "").strip()
            if vars_code:
                try:
                    exec(vars_code, {}, self._scope)
                    self.log_message.emit(f"       ✔ Değişkenler atandı.")
                except Exception as e:
                    self.log_message.emit(f"       ✗ Hata: {e}")
            
            next_node = self._get_next_node(node, 0)

        # ── PROCESS ──────────────────────────────────────────────────
        elif title == "Process":
            code = node.properties.get("code", "").strip()
            desc = node.properties.get("description", "")
            desc_str = f" ({desc})" if desc else ""
            self.log_message.emit(f"  [{step}] ⚙ PROCESS{desc_str} (ID: {short_id})")

            if code:
                try:
                    exec(code, {"__builtins__": __builtins__}, self._scope)
                    self.log_message.emit(f"       ✔ Çalıştırıldı.")
                except Exception as e:
                    self.log_message.emit(f"       ✗ Hata: {e}")
            
            next_node = self._get_next_node(node, 0)

        # ── DECISION ─────────────────────────────────────────────────
        elif title == "Decision":
            condition = node.properties.get("condition", "").strip()
            desc = node.properties.get("description", "")
            desc_str = f" ({desc})" if desc else ""
            self.log_message.emit(f"  [{step}] ❓ DECISION{desc_str} (ID: {short_id})")

            if condition:
                try:
                    result = eval(condition, {"__builtins__": __builtins__}, self._scope)
                    result_bool = bool(result)
                    self.log_message.emit(f"       Koşul: {condition} → {'✓ True' if result_bool else '✗ False'}")
                except Exception as e:
                    self.log_message.emit(f"       ✗ Hata: {e}")
                    result_bool = False
            else:
                self.log_message.emit(f"       ⚠ Koşul yok, atlanıyor (False sayıldı).")
                result_bool = False
                
            port_index = 0 if result_bool else 1
            next_node = self._get_next_node(node, port_index)

        # ── WHILE ────────────────────────────────────────────────────
        elif title == "While":
            condition = node.properties.get("condition", "").strip()
            desc = node.properties.get("description", "")
            desc_str = f" ({desc})" if desc else ""
            self.log_message.emit(f"  [{step}] 🔁 WHILE{desc_str} (ID: {short_id})")

            if condition:
                try:
                    result = eval(condition, {"__builtins__": __builtins__}, self._scope)
                    result_bool = bool(result)
                    self.log_message.emit(f"       Koşul: {condition} → {'✓ True (Loop)' if result_bool else '✗ False (Exit)'}")
                except Exception as e:
                    self.log_message.emit(f"       ✗ Koşul hatası: {e}")
                    result_bool = False
            else:
                self.log_message.emit(f"       ⚠ Döngü koşulu yok, atlanıyor (Exit).")
                result_bool = False
                
            # If True, loop body (port 0). If False, exit (port 1).
            port_index = 0 if result_bool else 1
            next_node = self._get_next_node(node, port_index)

        else:
            self.log_message.emit(f"  [{step}] 📦 {title} (ID: {short_id})")
            next_node = self._get_next_node(node, 0)

        # Değişken tablosunu güncelle
        self.scope_changed.emit(self._scope.copy())
        
        # Sonraki adıma hazırlan
        self._current_step += 1
        self._current_node = next_node
        
        # Eğer sonraki düğüm yoksa hemen bitir
        if not self._current_node:
            self._finish_flow()
        else:
            # Duraklatılmış moddaysak, sıradaki bekleyen düğümü vurgula
            if self._is_paused:
                self.highlight_node.emit(self._current_node)

    # ══════════════════════════════════════════════════════════════════
    #  Yardımcılar
    # ══════════════════════════════════════════════════════════════════

    def _get_next_node(self, current_node, port_index: int = 0):
        if port_index >= len(current_node.output_ports):
            return None
        source_port = current_node.output_ports[port_index]
        for edge in current_node.edges:
            if getattr(edge, 'source_port', None) is source_port:
                return edge.dest_node
        return None
