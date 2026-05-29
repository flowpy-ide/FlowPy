# core/interpreter.py
# ──────────────────────────────────────────────────────────────────────
# Interpreter : Sahnedeki düğüm akışını adımlı (State Machine) olarak çalıştırır.
# ──────────────────────────────────────────────────────────────────────

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QCoreApplication
from core.registry import NodeRegistry
from core.validator import FlowValidator
from core.i18n_nodes import resolve_canonical_node_title


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
        self._loop_stack: list = []
        self._current_node = None
        self._current_step = 0
        self._is_active = False
        self._is_paused = False
        self.MAX_STEPS = 500

        self._execution_delay_ms: int = 0
        self._step_timer = QTimer()
        self._step_timer.setSingleShot(True)
        self._step_timer.timeout.connect(self._do_next_step)
        self._pending_run = False
        self._breakpoints: set = set()

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

    def set_execution_speed(self, delay_ms: int):
        """0–2000 ms arası gecikme. 0 = tam hız."""
        self._execution_delay_ms = max(0, min(2000, delay_ms))

    def toggle_breakpoint(self, node_id: str):
        if node_id in self._breakpoints:
            self._breakpoints.discard(node_id)
        else:
            self._breakpoints.add(node_id)

    def has_breakpoint(self, node_id: str) -> bool:
        return node_id in self._breakpoints

    def run_flow(self):
        if not self._is_active:
            if not self._init_flow():
                return
        self._is_paused = False
        self.flow_state_changed.emit(True, False)
        self._log("Akış yürütülüyor…", "start")

        if self._execution_delay_ms > 0:
            self._pending_run = True
            self._schedule_next_step()
        else:
            while self._current_node and not self._is_paused:
                self._process_current_node()
                QCoreApplication.processEvents()

    def _schedule_next_step(self):
        if self._current_node and self._pending_run and not self._is_paused:
            self._step_timer.start(self._execution_delay_ms)

    def _do_next_step(self):
        if not self._current_node or not self._pending_run:
            return
        self._process_current_node()
        if self._current_node and self._pending_run and not self._is_paused:
            self._schedule_next_step()

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
        self._pending_run = False
        self._step_timer.stop()
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
        self._loop_stack = []
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
        title = resolve_canonical_node_title(getattr(node, "title", "?"))
        node_id = getattr(node, "node_id", "?")
        short_id = node_id[:8] if len(node_id) >= 8 else node_id

        if node_id in self._breakpoints and self._current_step > 1:
            self._is_paused = True
            self._pending_run = False
            self.flow_state_changed.emit(True, True)
            self._log(f"Breakpoint: {title} durdu.", "warning")
            self.highlight_node.emit(node)
            return

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
            if result_bool:
                self._push_loop(node)
                port_index = 0
            else:
                self._pop_loop(node)
                port_index = 1
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
                    self._push_loop(node)
                    self._for_states[node_id] += stp
                    next_node, edge = self._get_next_node(node, 0)
                else:
                    self._log_detail("       Döngü bitti (Exit).")
                    self._pop_loop(node)
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

        elif title == "Variable":
            p = node.properties
            name, value, typ = p.get("name", "x"), p.get("value", "0"), p.get("type", "auto")
            self._log_step(step, f"VARIABLE {name}{self._meta_suffix(p)} (ID: {short_id})", "process")
            try:
                if typ in ("int", "float", "str", "bool", "list"):
                    self._scope[name] = eval(f"{typ}({value})", {"__builtins__": __builtins__}, self._scope)
                else:
                    self._scope[name] = eval(value, {"__builtins__": __builtins__}, self._scope)
                self._log_detail(f"       ✔ {name} = {repr(self._scope[name])}")
            except Exception as e:
                self._log_detail(f"       ✗ Hata: {e}")
            next_node, edge = self._get_next_node(node, 0)

        elif title == "Math":
            p = node.properties
            r, a, op, b = p.get("result", "r"), p.get("operand_a", "a"), p.get("operator", "+"), p.get("operand_b", "b")
            self._log_step(step, f"MATH {r}{self._meta_suffix(p)} (ID: {short_id})", "process")
            try:
                self._scope[r] = eval(f"{a} {op} {b}", {"__builtins__": __builtins__}, self._scope)
                self._log_detail(f"       ✔ {r} = {self._scope[r]}")
            except Exception as e:
                self._log_detail(f"       ✗ Hata: {e}")
            next_node, edge = self._get_next_node(node, 0)

        elif title == "Print":
            expr = node.properties.get("expression", "").strip()
            self._log_step(step, f"PRINT{self._meta_suffix(node.properties)} (ID: {short_id})", "output")
            if expr:
                try:
                    res = eval(expr, {"__builtins__": __builtins__}, self._scope)
                    self._log_detail(f"       ► YAZDIR: {res}")
                except Exception as e:
                    self._log_detail(f"       ✗ Hata: {e}")
            next_node, edge = self._get_next_node(node, 0)

        elif title == "String Operation":
            p = node.properties
            var, op, args, res = p.get("variable", "s"), p.get("operation", "upper"), p.get("args", ""), p.get("result", "result")
            self._log_step(step, f"STRING {op}{self._meta_suffix(p)} (ID: {short_id})", "process")
            try:
                call = f"{var}.{op}({args})" if args else f"{var}.{op}()"
                self._scope[res] = eval(call, {"__builtins__": __builtins__}, self._scope)
                self._log_detail(f"       ✔ {res} = {repr(self._scope[res])}")
            except Exception as e:
                self._log_detail(f"       ✗ Hata: {e}")
            next_node, edge = self._get_next_node(node, 0)

        elif title == "Type Cast":
            p = node.properties
            src, tgt, res = p.get("source", "x"), p.get("target", "int"), p.get("result", "result")
            self._log_step(step, f"CAST {tgt}{self._meta_suffix(p)} (ID: {short_id})", "process")
            try:
                val = eval(src, {"__builtins__": __builtins__}, self._scope)
                caster = {"int": int, "float": float, "str": str, "bool": bool, "list": list}.get(tgt, int)
                self._scope[res] = caster(val)
                self._log_detail(f"       ✔ {res} = {repr(self._scope[res])}")
            except Exception as e:
                self._log_detail(f"       ✗ Hata: {e}")
            next_node, edge = self._get_next_node(node, 0)

        elif title == "List Operation":
            p = node.properties
            lv, op, args, res = p.get("list_var", "liste"), p.get("operation", "append"), p.get("args", ""), p.get("result", "")
            self._log_step(step, f"LIST {op}{self._meta_suffix(p)} (ID: {short_id})", "process")
            try:
                lst = eval(lv, {"__builtins__": __builtins__}, self._scope)
                scope = {"__builtins__": __builtins__}, self._scope
                if op == "len":
                    self._scope[res] = len(lst)
                elif op in ("sort", "reverse"):
                    getattr(lst, op)()
                    if res:
                        self._scope[res] = lst
                elif op in ("append", "insert", "remove") and args.strip():
                    val = eval(args.strip(), scope["__builtins__"], scope)
                    if op == "append":
                        lst.append(val)
                    elif op == "insert":
                        getattr(lst, op)(0, val)
                    else:
                        lst.remove(val)
                elif args.strip() and "," in args:
                    parts = [eval(p.strip(), scope["__builtins__"], scope) for p in args.split(",") if p.strip()]
                    getattr(lst, op)(*parts)
                elif args.strip():
                    getattr(lst, op)(eval(args.strip(), scope["__builtins__"], scope))
                else:
                    getattr(lst, op)()
                self._log_detail(f"       ✔ Liste işlemi: {op} → len={len(lst)}")
            except Exception as e:
                self._log_detail(f"       ✗ Hata: {e}")
            next_node, edge = self._get_next_node(node, 0)

        elif title == "If Elif Else":
            p = node.properties
            c_if, c_elif = p.get("condition_if", "").strip(), p.get("condition_elif", "").strip()
            self._log_step(step, f"IF/ELIF/ELSE{self._meta_suffix(p)} (ID: {short_id})", "decision")
            port_index = 2
            try:
                if c_if and bool(eval(c_if, {"__builtins__": __builtins__}, self._scope)):
                    port_index = 0
                    self._log_detail("       → if dalı")
                elif c_elif and bool(eval(c_elif, {"__builtins__": __builtins__}, self._scope)):
                    port_index = 1
                    self._log_detail("       → elif dalı")
                else:
                    self._log_detail("       → else dalı")
            except Exception as e:
                self._log_detail(f"       ✗ Hata: {e}")
            next_node, edge = self._get_next_node(node, port_index)

        elif title == "Break":
            p = node.properties
            self._log_step(step, f"BREAK{self._meta_suffix(p)} (ID: {short_id})", "while")
            next_node, edge = self._handle_break(node)

        elif title == "Continue":
            p = node.properties
            self._log_step(step, f"CONTINUE{self._meta_suffix(p)} (ID: {short_id})", "while")
            next_node, edge = self._handle_continue(node)

        elif title == "Try Except":
            p = node.properties
            self._log_step(step, f"TRY/EXCEPT{self._meta_suffix(p)} (ID: {short_id})", "process")
            self._log_detail("       → try gövdesi (port 0)")
            next_node, edge = self._get_next_node(node, 0)

        elif title == "Switch Match":
            p = node.properties
            var = p.get("variable", "x").strip()
            cases = [c.strip() for c in p.get("cases", "1,2,default").split(",") if c.strip()]
            self._log_step(step, f"SWITCH {var}{self._meta_suffix(p)} (ID: {short_id})", "decision")
            port_index = max(len(cases) - 1, 0)
            try:
                val = eval(var, {"__builtins__": __builtins__}, self._scope)
                for i, case in enumerate(cases):
                    if case == "default":
                        port_index = i
                        break
                    try:
                        case_val = eval(case, {"__builtins__": __builtins__}, self._scope)
                    except Exception:
                        case_val = case
                    if val == case_val:
                        port_index = i
                        break
                self._log_detail(f"       → port {port_index} ({cases[port_index] if port_index < len(cases) else '?'})")
            except Exception as e:
                self._log_detail(f"       ✗ Hata: {e}")
            next_node, edge = self._get_next_node(node, port_index)

        elif title == "Swap":
            p = node.properties
            a, b = p.get("var_a", "a"), p.get("var_b", "b")
            self._log_step(step, f"SWAP{self._meta_suffix(p)} (ID: {short_id})", "process")
            try:
                exec(
                    f"{a}, {b} = {b}, {a}",
                    {"__builtins__": __builtins__},
                    self._scope,
                )
                self._log_detail(f"       ✔ {a} ↔ {b}")
            except Exception as e:
                self._log_detail(f"       ✗ Hata: {e}")
            next_node, edge = self._get_next_node(node, 0)

        elif title == "Accumulate":
            p = node.properties
            acc, op, val = p.get("accumulator", "toplam"), p.get("operation", "+="), p.get("value", "x")
            self._log_step(step, f"ACCUMULATE{self._meta_suffix(p)} (ID: {short_id})", "process")
            try:
                exec(f"{acc} {op} {val}", {"__builtins__": __builtins__}, self._scope)
                self._log_detail(f"       ✔ {acc} = {self._scope.get(acc)}")
            except Exception as e:
                self._log_detail(f"       ✗ Hata: {e}")
            next_node, edge = self._get_next_node(node, 0)

        elif title == "Sort":
            p = node.properties
            lv = p.get("list_var", "liste")
            rev = p.get("reverse", "False")
            key = p.get("key", "").strip()
            self._log_step(step, f"SORT{self._meta_suffix(p)} (ID: {short_id})", "process")
            try:
                lst = eval(lv, {"__builtins__": __builtins__}, self._scope)
                kwargs = {"reverse": bool(eval(rev, {"__builtins__": __builtins__}, self._scope))}
                if key:
                    kwargs["key"] = eval(f"lambda x: {key}", {"__builtins__": __builtins__}, self._scope)
                lst.sort(**kwargs)
                self._log_detail("       ✔ Liste sıralandı")
            except Exception as e:
                self._log_detail(f"       ✗ Hata: {e}")
            next_node, edge = self._get_next_node(node, 0)

        elif title == "Search":
            p = node.properties
            lv, tgt, res = p.get("list_var", "liste"), p.get("target", "hedef"), p.get("result", "index")
            self._log_step(step, f"SEARCH{self._meta_suffix(p)} (ID: {short_id})", "process")
            try:
                lst = eval(lv, {"__builtins__": __builtins__}, self._scope)
                target = eval(tgt, {"__builtins__": __builtins__}, self._scope)
                self._scope[res] = lst.index(target) if target in lst else -1
                self._log_detail(f"       ✔ {res} = {self._scope[res]}")
            except Exception as e:
                self._log_detail(f"       ✗ Hata: {e}")
            next_node, edge = self._get_next_node(node, 0)

        elif title == "Random":
            p = node.properties
            import random
            op, args, res = p.get("operation", "randint"), p.get("args", "1,100"), p.get("result", "r")
            self._log_step(step, f"RANDOM{self._meta_suffix(p)} (ID: {short_id})", "process")
            try:
                self._scope[res] = eval(f"random.{op}({args})", {"random": random, "__builtins__": __builtins__}, self._scope)
                self._log_detail(f"       ✔ {res} = {self._scope[res]}")
            except Exception as e:
                self._log_detail(f"       ✗ Hata: {e}")
            next_node, edge = self._get_next_node(node, 0)

        elif title == "Lambda":
            p = node.properties
            name, params, body = p.get("name", "f"), p.get("params", "x"), p.get("body", "x")
            self._log_step(step, f"LAMBDA {name}{self._meta_suffix(p)} (ID: {short_id})", "process")
            try:
                self._scope[name] = eval(f"lambda {params}: {body}", {"__builtins__": __builtins__}, self._scope)
                self._log_detail(f"       ✔ {name} tanımlandı")
            except Exception as e:
                self._log_detail(f"       ✗ Hata: {e}")
            next_node, edge = self._get_next_node(node, 0)

        elif title == "List Comprehension":
            p = node.properties
            res, expr, var, it, cond = (
                p.get("result", "s"), p.get("expression", "x"), p.get("variable", "x"),
                p.get("iterable", "liste"), p.get("condition", ""),
            )
            self._log_step(step, f"LIST COMP{self._meta_suffix(p)} (ID: {short_id})", "process")
            try:
                if cond:
                    self._scope[res] = eval(
                        f"[{expr} for {var} in {it} if {cond}]",
                        {"__builtins__": __builtins__}, self._scope,
                    )
                else:
                    self._scope[res] = eval(
                        f"[{expr} for {var} in {it}]",
                        {"__builtins__": __builtins__}, self._scope,
                    )
                self._log_detail(f"       ✔ {res} = {self._scope[res]}")
            except Exception as e:
                self._log_detail(f"       ✗ Hata: {e}")
            next_node, edge = self._get_next_node(node, 0)

        elif title == "Assert":
            p = node.properties
            cond, msg = p.get("condition", "True"), p.get("message", "Assertion failed")
            self._log_step(step, f"ASSERT{self._meta_suffix(p)} (ID: {short_id})", "decision")
            port_index = 0
            try:
                if not bool(eval(cond, {"__builtins__": __builtins__}, self._scope)):
                    raise AssertionError(msg)
                self._log_detail("       ✔ Assert geçti")
            except AssertionError as e:
                self._log_detail(f"       ✗ Assert başarısız: {e}")
                port_index = 1
            except Exception as e:
                self._log_detail(f"       ✗ Hata: {e}")
                port_index = 1
            next_node, edge = self._get_next_node(node, port_index)

        elif title == "Import":
            p = node.properties
            mod, alias, frm = p.get("module", "math"), p.get("alias", ""), p.get("from_import", "")
            self._log_step(step, f"IMPORT {mod}{self._meta_suffix(p)} (ID: {short_id})", "process")
            try:
                if frm:
                    exec(f"from {mod} import {frm}", {"__builtins__": __builtins__}, self._scope)
                elif alias:
                    exec(f"import {mod} as {alias}", {"__builtins__": __builtins__}, self._scope)
                else:
                    exec(f"import {mod}", {"__builtins__": __builtins__}, self._scope)
                self._log_detail("       ✔ Import tamam")
            except Exception as e:
                self._log_detail(f"       ✗ Hata: {e}")
            next_node, edge = self._get_next_node(node, 0)

        elif title == "File Read":
            p = node.properties
            fp, var, mode = p.get("filepath", "dosya.txt"), p.get("variable", "icerik"), p.get("mode", "all")
            self._log_step(step, f"FILE READ{self._meta_suffix(p)} (ID: {short_id})", "process")
            try:
                read_fn = {"all": "read", "lines": "readlines", "line": "readline"}.get(mode, "read")
                with open(fp, "r", encoding="utf-8") as f:
                    self._scope[var] = getattr(f, read_fn)()
                self._log_detail(f"       ✔ {var} okundu")
            except Exception as e:
                self._log_detail(f"       ✗ Hata: {e}")
            next_node, edge = self._get_next_node(node, 0)

        elif title == "File Write":
            p = node.properties
            fp, expr, mode = p.get("filepath", "cikti.txt"), p.get("expression", ""), p.get("mode", "w")
            self._log_step(step, f"FILE WRITE{self._meta_suffix(p)} (ID: {short_id})", "process")
            try:
                val = eval(expr, {"__builtins__": __builtins__}, self._scope) if expr else ""
                with open(fp, mode, encoding="utf-8") as f:
                    f.write(str(val))
                self._log_detail("       ✔ Dosyaya yazıldı")
            except Exception as e:
                self._log_detail(f"       ✗ Hata: {e}")
            next_node, edge = self._get_next_node(node, 0)

        elif title == "Delay":
            import time
            secs = float(eval(node.properties.get("seconds", "1"), {"__builtins__": __builtins__}, self._scope))
            self._log_step(step, f"DELAY {secs}s{self._meta_suffix(node.properties)} (ID: {short_id})", "info")
            time.sleep(min(max(secs, 0), 10))
            QCoreApplication.processEvents()
            next_node, edge = self._get_next_node(node, 0)

        elif title == "Stop":
            msg = node.properties.get("message", "").strip()
            self._log_step(step, f"STOP{self._meta_suffix(node.properties)} (ID: {short_id})", "stop")
            if msg:
                self._log_detail(f"       ► {msg}")
            next_node, edge = None, None

        elif title in ("Comment", "Group"):
            self._log_step(step, f"{title} (atlandı) (ID: {short_id})", "info")
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

    def _meta_suffix(self, props: dict) -> str:
        tag = props.get("tag", "").strip()
        desc = props.get("description", "").strip()
        if tag and desc:
            return f" [{tag}: {desc}]"
        if tag:
            return f" [{tag}]"
        if desc:
            return f" ({desc})"
        return ""

    def _push_loop(self, node):
        if not self._loop_stack or self._loop_stack[-1].node_id != node.node_id:
            self._loop_stack.append(node)

    def _pop_loop(self, node):
        if self._loop_stack and self._loop_stack[-1].node_id == node.node_id:
            self._loop_stack.pop()

    def _handle_break(self, node) -> tuple:
        if not self._loop_stack:
            self._log_detail("       ⚠ break döngü dışında — normal akışa devam.")
            return self._get_next_node(node, 0)
        loop = self._loop_stack[-1]
        self._pop_loop(loop)
        if loop.title == "For" and loop.node_id in self._for_states:
            del self._for_states[loop.node_id]
        self._log_detail(f"       ✔ Döngüden çıkıldı ({loop.title})")
        return self._get_next_node(loop, 1)

    def _handle_continue(self, node) -> tuple:
        if not self._loop_stack:
            self._log_detail("       ⚠ continue döngü dışında — normal akışa devam.")
            return self._get_next_node(node, 0)
        loop = self._loop_stack[-1]
        self._log_detail(f"       ✔ Sonraki tur ({loop.title})")
        return loop, None

    def _get_next_node(self, current_node, port_index: int = 0) -> tuple:
        if port_index >= len(current_node.output_ports):
            return None, None
        source_port = current_node.output_ports[port_index]
        for edge in current_node.edges:
            if getattr(edge, 'source_port', None) is source_port:
                return edge.dest_node, edge
        return None, None
