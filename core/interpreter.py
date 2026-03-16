# core/interpreter.py
# ──────────────────────────────────────────────────────────────────────
# Interpreter : Sahnedeki düğüm akışını adımlı (State Machine) olarak
#               çalıştıran motor.
# ──────────────────────────────────────────────────────────────────────

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QCoreApplication
from core.registry import NodeRegistry
from core.validator import FlowValidator

class Interpreter(QObject):
    """Registry'deki düğümleri state machine yapısıyla çalıştıran yorumlayıcı."""

    log_message = pyqtSignal(str)
    highlight_node = pyqtSignal(object)       
    highlight_edge = pyqtSignal(object)       
    clear_highlights = pyqtSignal()           
    
    # Yeni sinyaller: Debugger ve Watcher için
    scope_changed = pyqtSignal(dict)
    flow_state_changed = pyqtSignal(bool, bool)  # (is_active, is_paused)

    def __init__(self, registry: NodeRegistry, parent=None):
        super().__init__(parent)
        self.registry = registry
        self._scope: dict = {}
        self._for_states: dict = {}
        
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
        """Sahnede Start düğümünü bulur, grafı doğrular ve state'i sıfırlar."""
        self.clear_highlights.emit()
        
        # 1. Grafı doğrula
        validator = FlowValidator(self.registry)
        errors = validator.validate()
        
        if errors:
            self.log_message.emit("═" * 50)
            self.log_message.emit("❌ AKIŞ DOĞRULAMA HATASI")
            self.log_message.emit("═" * 50)
            for err in errors:
                err_msg = str(err)
                if hasattr(err, "node") and err.node:
                    self.highlight_node.emit(err.node) # Hatalı düğümü vurgula
                self.log_message.emit(f"   ▶ {err_msg}")
            
            self.log_message.emit("⚠ Çalıştırma iptal edildi. Lütfen hataları düzeltin.")
            return False

        # 2. Start düğümünü bul
        nodes = self.registry.get_all_nodes()
        start_node = None
        for node_id, node in nodes.items():
            if getattr(node, "title", "") == "Start":
                start_node = node
                break

        if not start_node:
            self.log_message.emit("⚠  Akışta bir 'Start' düğümü bulunamadı!")
            return False

        self._scope = {}
        self._for_states = {}
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
            
            next_node, edge = self._get_next_node(node, 0)

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
            
            next_node, edge = self._get_next_node(node, 0)

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
            next_node, edge = self._get_next_node(node, port_index)

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
            next_node, edge = self._get_next_node(node, port_index)

        # ── INPUT ────────────────────────────────────────────────────
        elif title == "Input":
            var_name = node.properties.get("variable", "USER_IN").strip()
            prompt_text = node.properties.get("prompt", "Değer girin:")
            self.log_message.emit(f"  [{step}] ⌨ INPUT (ID: {short_id})")

            from PyQt6.QtWidgets import QInputDialog
            text, ok = QInputDialog.getText(None, "Giriş (Input)", prompt_text)
            
            if ok:
                if text.isdigit():
                    val = int(text)
                else:
                    try:
                        val = float(text)
                    except ValueError:
                        val = text
                self._scope[var_name] = val
                self.log_message.emit(f"       ✔ '{var_name}' değişkenine {val} atandı.")
            else:
                self.log_message.emit(f"       ⚠ İptal edildi, {var_name} = None")
                self._scope[var_name] = None
                
            next_node, edge = self._get_next_node(node, 0)

        # ── OUTPUT ───────────────────────────────────────────────────
        elif title == "Output":
            expr = node.properties.get("expression", "").strip()
            self.log_message.emit(f"  [{step}] 📢 OUTPUT (ID: {short_id})")

            if expr:
                try:
                    res = eval(expr, {"__builtins__": __builtins__}, self._scope)
                    self.log_message.emit(f"       ► ÇIKTI: {res}")
                except Exception as e:
                    self.log_message.emit(f"       ✗ Çıktı Hatası: {e}")
            else:
                self.log_message.emit(f"       ⚠ Çıktı ifadesi boş.")
                
            next_node, edge = self._get_next_node(node, 0)

        # ── FOR LOOP ─────────────────────────────────────────────────
        elif title == "For":
            var_name = node.properties.get("variable", "i").strip()
            start_val = node.properties.get("start", "0").strip()
            end_val = node.properties.get("end", "10").strip()
            step_val = node.properties.get("step", "1").strip()
            self.log_message.emit(f"  [{step}] 🔁 FOR LOOP (ID: {short_id})")

            try:
                s = int(eval(start_val, {"__builtins__": __builtins__}, self._scope))
                e = int(eval(end_val, {"__builtins__": __builtins__}, self._scope))
                stp = int(eval(step_val, {"__builtins__": __builtins__}, self._scope))
                
                if node_id not in self._for_states:
                    self._for_states[node_id] = s
                
                curr = self._for_states[node_id]
                self._scope[var_name] = curr
                
                condition_met = (curr < e) if stp > 0 else (curr > e)
                
                if condition_met:
                    self.log_message.emit(f"       Döngü adımı: {var_name} = {curr} (Loop)")
                    self._for_states[node_id] += stp
                    next_node, edge = self._get_next_node(node, 0) # Loop branch
                else:
                    self.log_message.emit(f"       Döngü bitti (Exit).")
                    del self._for_states[node_id]
                    next_node, edge = self._get_next_node(node, 1) # Exit branch
                    
            except Exception as ex:
                self.log_message.emit(f"       ✗ For döngüsü hatası: {ex}")
                next_node, edge = self._get_next_node(node, 1)

        # ── FUNCTION ─────────────────────────────────────────────────
        elif title == "Function":
            func_name = node.properties.get("function_name", "my_func").strip()
            params = node.properties.get("parameters", "").strip()
            self.log_message.emit(f"  [{step}] 📋 FUNCTION: {func_name}({params}) (ID: {short_id})")
            next_node, edge = self._get_next_node(node, 0)

        # ── RETURN ───────────────────────────────────────────────────
        elif title == "Return":
            expr = node.properties.get("expression", "").strip()
            self.log_message.emit(f"  [{step}] ↩ RETURN (ID: {short_id})")
            if expr:
                try:
                    res = eval(expr, {"__builtins__": __builtins__}, self._scope)
                    self.log_message.emit(f"       ► Dönüş Değeri: {res}")
                except Exception as e:
                    self.log_message.emit(f"       ✗ Return Hatası: {e}")
            next_node, edge = self._get_next_node(node, 0)

        else:
            self.log_message.emit(f"  [{step}] 📦 {title} (ID: {short_id})")
            next_node, edge = self._get_next_node(node, 0)

        # Hangi edge'den geçiş yaptıysak onu vurgula
        if edge:
            self.highlight_edge.emit(edge)

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

    def _get_next_node(self, current_node, port_index: int = 0) -> tuple:
        """Belirtilen porttan çıkan hedef düğümü ve kenarı (Node, Edge) döner."""
        if port_index >= len(current_node.output_ports):
            return None, None
        source_port = current_node.output_ports[port_index]
        for edge in current_node.edges:
            if getattr(edge, 'source_port', None) is source_port:
                return edge.dest_node, edge
        return None, None
