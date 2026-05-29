# core/interpreter.py
# ──────────────────────────────────────────────────────────────────────
# Interpreter : Sahnedeki düğüm akışını adımlı (State Machine) olarak çalıştırır.
# ──────────────────────────────────────────────────────────────────────

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QCoreApplication
from core.registry import NodeRegistry
from core.validator import FlowValidator


class Interpreter(QObject):
    """Registry'deki düğümleri state machine yapısıyla çalıştıran yorumlayıcı."""

    _LOG_COLORS = {
        "start":    ("#4ade80", "▶"),
        "input":    ("#60a5fa", "⌨"),
        "process":  ("#a78bfa", "⚙"),
        "decision": ("#fbbf24", "❓"),
        "while":    ("#a78bfa", "🔁"),
        "for":      ("#a78bfa", "🔁"),
        "output":   ("#4ade80", "📢"),
        "function": ("#f472b6", "📋"),
        "return":   ("#f472b6", "↩"),
        "success":  ("#22c55e", "✔"),
        "error":    ("#ef4444", "✗"),
        "warning":  ("#f59e0b", "⚠"),
        "info":     ("#888888", "·"),
        "header":   ("#444444", "─"),
        "complete": ("#22c55e", "✔"),
        "stop":     ("#888888", "⏹"),
    }

    log_message = pyqtSignal(str)
    highlight_node = pyqtSignal(object)
    highlight_edge = pyqtSignal(object)
    clear_highlights = pyqtSignal()
    scope_changed = pyqtSignal(dict)
    flow_state_changed = pyqtSignal(bool, bool)

    def __init__(self, registry: NodeRegistry, parent=None):
        super().__init__(parent)
        self.registry = registry
        self._scope: dict = {}
        self._for_states: dict = {}
        self._current_node = None
        self._current_step = 0
        self._is_active = False
        self._is_paused = False
        self.MAX_STEPS = 500

    def _log(self, msg: str, level: str = "info"):
        color, icon = self._LOG_COLORS.get(level, ("#888888", "·"))
        self.log_message.emit(
            f'<span style="color:{color};font-family:Consolas,monospace;'
            f'font-size:11px">{icon} {msg}</span>'
        )

    def _log_step(self, step: int, msg: str, level: str):
        color, icon = self._LOG_COLORS.get(level, ("#888888", "·"))
        self.log_message.emit(
            f'<span style="color:#3a3a3a;font-size:10px">[{step}]</span> '
            f'<span style="color:{color};font-family:Consolas,monospace;'
            f'font-size:11px">{icon} {msg}</span>'
        )

    def _log_detail(self, msg: str):
        level = "info"
        if "✔" in msg:
            level = "success"
        elif "✗" in msg:
            level = "error"
        elif "⚠" in msg:
            level = "warning"
        elif "►" in msg:
            level = "output"
        self._log(msg.strip(), level)

    def run_flow(self):
        if not self._is_active:
            if not self._init_flow():
                return
        self._is_paused = False
        self.flow_state_changed.emit(True, False)
        self._log("Akış yürütülüyor…", "start")
        while self._current_node and not self._is_paused:
            self._process_current_node()
            QCoreApplication.processEvents()

    def step_flow(self):
        if not self._is_active:
            if not self._init_flow():
                return
        self._is_paused = True
        self.flow_state_changed.emit(True, True)
        self._process_current_node()

    def stop_flow(self):
        if not self._is_active:
            return
        self._is_active = False
        self._is_paused = False
        self._current_node = None
        self.flow_state_changed.emit(False, False)
        self.clear_highlights.emit()
        self._log("Çalıştırma durduruldu.", "stop")

    def _init_flow(self) -> bool:
        self.clear_highlights.emit()
        validator = FlowValidator(self.registry)
        errors = validator.validate()

        if errors:
            self._log("═" * 50, "header")
            self._log("AKIŞ DOĞRULAMA HATASI", "error")
            self._log("═" * 50, "header")
            for err in errors:
                err_msg = str(err)
                if hasattr(err, "node") and err.node:
                    self.highlight_node.emit(err.node)
                self._log(err_msg, "error")
            self._log("Çalıştırma iptal edildi. Lütfen hataları düzeltin.", "warning")
            return False

        nodes = self.registry.get_all_nodes()
        start_node = None
        for node_id, node in nodes.items():
            if getattr(node, "title", "") == "Start":
                start_node = node
                break

        if not start_node:
            self._log("Akışta bir 'Start' düğümü bulunamadı!", "warning")
            return False

        self._scope = {}
        self._for_states = {}
        self.scope_changed.emit(self._scope)
        self._current_step = 1
        self._current_node = start_node
        self._is_active = True

        self._log("═" * 50, "header")
        self._log("Oturum Başladı", "start")
        self._log("═" * 50, "header")
        self.highlight_node.emit(self._current_node)
        return True

    def _finish_flow(self):
        self._log("═" * 50, "header")
        self._log("Akış tamamlandı.", "complete")
        self._log(f"Sonuç Değişkenler: {self._scope}", "info")
        self._log("", "info")

        self._is_active = False
        self._is_paused = False
        self._current_node = None
        self.flow_state_changed.emit(False, False)
        QTimer.singleShot(1500, self.clear_highlights.emit)

    def _process_current_node(self):
        if not self._current_node:
            self._finish_flow()
            return

        if self._current_step > self.MAX_STEPS:
            self._log("Maksimum adım sayısına ulaşıldı (sonsuz döngü?)", "warning")
            self.stop_flow()
            return

        node = self._current_node
        step = self._current_step
        title = getattr(node, "title", "?")
        node_id = getattr(node, "node_id", "?")
        short_id = node_id[:8] if len(node_id) >= 8 else node_id

        self.highlight_node.emit(node)
        next_node = None
        edge = None

        if title == "Start":
            self._log_step(step, f"START (ID: {short_id})", "start")
            vars_code = node.properties.get("variables", "").strip()
            if vars_code:
                try:
                    exec(vars_code, {}, self._scope)
                    self._log_detail("       ✔ Değişkenler atandı.")
                except Exception as e:
                    self._log_detail(f"       ✗ Hata: {e}")
            next_node, edge = self._get_next_node(node, 0)

        elif title == "Process":
            code = node.properties.get("code", "").strip()
            desc = node.properties.get("description", "")
            desc_str = f" ({desc})" if desc else ""
            self._log_step(step, f"PROCESS{desc_str} (ID: {short_id})", "process")
            if code:
                try:
                    exec(code, {"__builtins__": __builtins__}, self._scope)
                    self._log_detail("       ✔ Çalıştırıldı.")
                except Exception as e:
                    self._log_detail(f"       ✗ Hata: {e}")
            next_node, edge = self._get_next_node(node, 0)

        elif title == "Decision":
            condition = node.properties.get("condition", "").strip()
            desc = node.properties.get("description", "")
            desc_str = f" ({desc})" if desc else ""
            self._log_step(step, f"DECISION{desc_str} (ID: {short_id})", "decision")
            if condition:
                try:
                    result = eval(condition, {"__builtins__": __builtins__}, self._scope)
                    result_bool = bool(result)
                    mark = "✓ True" if result_bool else "✗ False"
                    self._log_detail(f"       Koşul: {condition} → {mark}")
                except Exception as e:
                    self._log_detail(f"       ✗ Hata: {e}")
                    result_bool = False
            else:
                self._log_detail("       ⚠ Koşul yok, atlanıyor (False sayıldı).")
                result_bool = False
            port_index = 0 if result_bool else 1
            next_node, edge = self._get_next_node(node, port_index)

        elif title == "While":
            condition = node.properties.get("condition", "").strip()
            desc = node.properties.get("description", "")
            desc_str = f" ({desc})" if desc else ""
            self._log_step(step, f"WHILE{desc_str} (ID: {short_id})", "while")
            if condition:
                try:
                    result = eval(condition, {"__builtins__": __builtins__}, self._scope)
                    result_bool = bool(result)
                    mark = "✓ True (Loop)" if result_bool else "✗ False (Exit)"
                    self._log_detail(f"       Koşul: {condition} → {mark}")
                except Exception as e:
                    self._log_detail(f"       ✗ Koşul hatası: {e}")
                    result_bool = False
            else:
                self._log_detail("       ⚠ Döngü koşulu yok, atlanıyor (Exit).")
                result_bool = False
            port_index = 0 if result_bool else 1
            next_node, edge = self._get_next_node(node, port_index)

        elif title == "Input":
            var_name = node.properties.get("variable", "USER_IN").strip()
            prompt_text = node.properties.get("prompt", "Değer girin:")
            input_type = node.properties.get("input_type", "auto").strip()
            self._log_step(step, f"INPUT (ID: {short_id})", "input")

            from PyQt6.QtWidgets import QInputDialog
            text, ok = QInputDialog.getText(None, f"Giriş — {var_name}", prompt_text)

            if ok:
                try:
                    if input_type == "int":
                        val = int(text)
                    elif input_type == "float":
                        val = float(text)
                    elif input_type == "str":
                        val = str(text)
                    else:
                        if text.lstrip("-").isdigit():
                            val = int(text)
                        else:
                            try:
                                val = float(text)
                            except ValueError:
                                val = text
                except ValueError:
                    self._log_detail(
                        f"       ⚠ '{text}' değeri '{input_type}' tipine "
                        f"dönüştürülemedi, string olarak atandı."
                    )
                    val = text
                self._scope[var_name] = val
                self._log_detail(
                    f"       ✔ '{var_name}' = {repr(val)} ({type(val).__name__})"
                )
            else:
                self._log_detail(f"       ⚠ İptal edildi, {var_name} = None")
                self._scope[var_name] = None
            next_node, edge = self._get_next_node(node, 0)

        elif title == "Output":
            expr = node.properties.get("expression", "").strip()
            self._log_step(step, f"OUTPUT (ID: {short_id})", "output")
            if expr:
                try:
                    res = eval(expr, {"__builtins__": __builtins__}, self._scope)
                    self._log_detail(f"       ► ÇIKTI: {res}")
                except Exception as e:
                    self._log_detail(f"       ✗ Çıktı Hatası: {e}")
            else:
                self._log_detail("       ⚠ Çıktı ifadesi boş.")
            next_node, edge = self._get_next_node(node, 0)

        elif title == "For":
            var_name = node.properties.get("variable", "i").strip()
            start_val = node.properties.get("start", "0").strip()
            end_val = node.properties.get("end", "10").strip()
            step_val = node.properties.get("step", "1").strip()
            self._log_step(step, f"FOR LOOP (ID: {short_id})", "for")
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
                    self._log_detail(f"       Döngü adımı: {var_name} = {curr} (Loop)")
                    self._for_states[node_id] += stp
                    next_node, edge = self._get_next_node(node, 0)
                else:
                    self._log_detail("       Döngü bitti (Exit).")
                    del self._for_states[node_id]
                    next_node, edge = self._get_next_node(node, 1)
            except Exception as ex:
                self._log_detail(f"       ✗ For döngüsü hatası: {ex}")
                next_node, edge = self._get_next_node(node, 1)

        elif title == "Function":
            func_name = node.properties.get("function_name", "my_func").strip()
            params = node.properties.get("parameters", "").strip()
            self._log_step(
                step, f"FUNCTION: {func_name}({params}) (ID: {short_id})", "function"
            )
            next_node, edge = self._get_next_node(node, 0)

        elif title == "Return":
            expr = node.properties.get("expression", "").strip()
            self._log_step(step, f"RETURN (ID: {short_id})", "return")
            if expr:
                try:
                    res = eval(expr, {"__builtins__": __builtins__}, self._scope)
                    self._log_detail(f"       ► Dönüş Değeri: {res}")
                except Exception as e:
                    self._log_detail(f"       ✗ Return Hatası: {e}")
            next_node, edge = self._get_next_node(node, 0)

        else:
            self._log_step(step, f"{title} (ID: {short_id})", "info")
            next_node, edge = self._get_next_node(node, 0)

        if edge:
            self.highlight_edge.emit(edge)
        self.scope_changed.emit(self._scope.copy())
        self._current_step += 1
        self._current_node = next_node

        if not self._current_node:
            self._finish_flow()
        elif self._is_paused:
            self.highlight_node.emit(self._current_node)

    def _get_next_node(self, current_node, port_index: int = 0) -> tuple:
        if port_index >= len(current_node.output_ports):
            return None, None
        source_port = current_node.output_ports[port_index]
        for edge in current_node.edges:
            if getattr(edge, 'source_port', None) is source_port:
                return edge.dest_node, edge
        return None, None
