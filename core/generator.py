"""
core/generator.py
──────────────────────────────────────────────────────────────────────
CodeGenerator : Flow graph'ını Python, Java, C, C++,
                JavaScript, Pseudocode'a çevirir.
──────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from core.registry import NodeRegistry

SUPPORTED_LANGUAGES = ["Python", "Java", "C", "C++", "JavaScript", "Pseudocode"]


class CodeGenerator:
    def __init__(self, registry: NodeRegistry):
        self.registry = registry

    @staticmethod
    def _annotation_lines(props: dict, indent: str) -> list[str]:
        """Etiket / açıklama alanlarını üretilen koda yorum olarak ekler."""
        lines: list[str] = []
        tag = props.get("tag", "").strip()
        desc = props.get("description", "").strip()
        if tag:
            lines.append(f"{indent}# @tag: {tag}")
        if desc:
            for ln in desc.splitlines():
                lines.append(f"{indent}# {ln.strip()}")
        return lines

    def generate(self, lang: str) -> str:
        nodes = self._get_ordered_nodes()
        if not nodes:
            return "# Henüz node yok\n"

        generators = {
            "Python": self._gen_python,
            "Java": self._gen_java,
            "C": self._gen_c,
            "C++": self._gen_cpp,
            "JavaScript": self._gen_js,
            "Pseudocode": self._gen_pseudo,
        }
        gen_fn = generators.get(lang, self._gen_python)
        return gen_fn(nodes)

    def _get_ordered_nodes(self):
        """Start'tan başlayarak BFS ile sıralı node listesi döner."""
        nodes = self.registry.get_all_nodes()
        if not nodes:
            return []
        start = next((n for n in nodes.values() if n.title == "Start"), None)
        if not start:
            return list(nodes.values())

        visited, ordered = set(), []
        queue = [start]
        while queue:
            node = queue.pop(0)
            if node.node_id in visited:
                continue
            visited.add(node.node_id)
            ordered.append(node)
            for edge in node.edges:
                if edge.source_node is node and edge.dest_node:
                    queue.append(edge.dest_node)
        return ordered

    # ── PYTHON ───────────────────────────────────────────────────────

    def _gen_python(self, nodes) -> str:
        lines = ["# FlowPy Tarafından Üretilen Python Kodu", "", "def main():"]
        indent = "    "

        for node in nodes:
            t = node.title
            p = node.properties
            if t != "Comment":
                lines.extend(self._annotation_lines(p, indent))

            if t == "Start":
                vars_code = p.get("variables", "").strip()
                if vars_code:
                    for v in vars_code.split("\n"):
                        lines.append(f"{indent}{v.strip()}")
            elif t == "Variable":
                name = p.get("name", "x")
                value = p.get("value", "0")
                cast = p.get("type", "auto")
                if cast in ("int", "float", "str", "bool", "list"):
                    lines.append(f"{indent}{name} = {cast}({value})")
                else:
                    lines.append(f"{indent}{name} = {value}")
            elif t == "Process":
                for line in p.get("code", "").strip().split("\n"):
                    if line.strip():
                        lines.append(f"{indent}{line.strip()}")
            elif t == "Print":
                expr = p.get("expression", "")
                end = p.get("end", "\\n").replace("\\n", "\n")
                end_arg = ', end=""' if end == "" else ""
                lines.append(f"{indent}print({expr}{end_arg})")
            elif t == "Math":
                r, a, op, b = (
                    p.get("result", "r"),
                    p.get("operand_a", "a"),
                    p.get("operator", "+"),
                    p.get("operand_b", "b"),
                )
                lines.append(f"{indent}{r} = {a} {op} {b}")
            elif t == "String Operation":
                var, op, args, res = (
                    p.get("variable", "s"),
                    p.get("operation", "upper"),
                    p.get("args", ""),
                    p.get("result", "result"),
                )
                args_str = f"({args})" if args else "()"
                lines.append(f"{indent}{res} = {var}.{op}{args_str}")
            elif t == "Type Cast":
                src, tgt, res = p.get("source", "x"), p.get("target", "int"), p.get("result", "result")
                lines.append(f"{indent}{res} = {tgt}({src})")
            elif t == "List Operation":
                lv, op, args, res = (
                    p.get("list_var", "liste"),
                    p.get("operation", "append"),
                    p.get("args", ""),
                    p.get("result", ""),
                )
                if op == "len":
                    lines.append(f"{indent}{res} = len({lv})")
                elif op in ("sort", "reverse"):
                    lines.append(f"{indent}{lv}.{op}()")
                elif args:
                    lines.append(f"{indent}{lv}.{op}({args})")
                else:
                    lines.append(f"{indent}{lv}.{op}()")
            elif t == "Input":
                var, prompt, typ = (
                    p.get("variable", "x"),
                    p.get("prompt", "Girin:"),
                    p.get("input_type", "auto"),
                )
                cast = f"{typ}(" if typ in ("int", "float", "str") else ""
                close = ")" if cast else ""
                lines.append(f"{indent}{var} = {cast}input('{prompt}'){close}")
            elif t == "Output":
                lines.append(f"{indent}print({p.get('expression', '')})")
            elif t == "Decision":
                lines.append(f"{indent}if {p.get('condition', 'True')}:")
                lines.append(f"{indent}    pass  # True branch")
                lines.append(f"{indent}else:")
                lines.append(f"{indent}    pass  # False branch")
            elif t == "If Elif Else":
                lines.append(f"{indent}if {p.get('condition_if', 'True')}:")
                lines.append(f"{indent}    pass  # if branch")
                lines.append(f"{indent}elif {p.get('condition_elif', 'False')}:")
                lines.append(f"{indent}    pass  # elif branch")
                lines.append(f"{indent}else:")
                lines.append(f"{indent}    pass  # else branch")
            elif t == "While":
                lines.append(f"{indent}while {p.get('condition', 'True')}:")
                lines.append(f"{indent}    pass  # loop body")
            elif t == "For":
                v, s, e, stp = (
                    p.get("variable", "i"),
                    p.get("start", "0"),
                    p.get("end", "10"),
                    p.get("step", "1"),
                )
                lines.append(f"{indent}for {v} in range({s}, {e}, {stp}):")
                lines.append(f"{indent}    pass  # loop body")
            elif t == "Break":
                lines.append(f"{indent}break")
            elif t == "Continue":
                lines.append(f"{indent}continue")
            elif t == "Try Except":
                exc = p.get("exception_type", "Exception")
                err = p.get("error_var", "e")
                lines.append(f"{indent}try:")
                lines.append(f"{indent}    pass  # try body")
                lines.append(f"{indent}except {exc} as {err}:")
                lines.append(f"{indent}    pass  # except body")
            elif t == "Switch Match":
                var = p.get("variable", "x")
                cases = [c.strip() for c in p.get("cases", "").split(",") if c.strip()]
                lines.append(f"{indent}match {var}:")
                for case in cases:
                    if case == "default":
                        lines.append(f"{indent}    case _:")
                    else:
                        lines.append(f"{indent}    case {case}:")
                    lines.append(f"{indent}        pass")
            elif t == "Swap":
                a, b = p.get("var_a", "a"), p.get("var_b", "b")
                lines.append(f"{indent}{a}, {b} = {b}, {a}")
            elif t == "Accumulate":
                acc, op, val = p.get("accumulator", "toplam"), p.get("operation", "+="), p.get("value", "x")
                lines.append(f"{indent}{acc} {op} {val}")
            elif t == "Sort":
                lv = p.get("list_var", "liste")
                rev = p.get("reverse", "False")
                key = p.get("key", "")
                key_arg = f", key={key}" if key else ""
                lines.append(f"{indent}{lv}.sort(reverse={rev}{key_arg})")
            elif t == "Search":
                lv, tgt, res = p.get("list_var", "liste"), p.get("target", "hedef"), p.get("result", "index")
                lines.append(f"{indent}{res} = {lv}.index({tgt}) if {tgt} in {lv} else -1")
            elif t == "Random":
                op, args, res = p.get("operation", "randint"), p.get("args", "1,100"), p.get("result", "r")
                lines.append(f"{indent}import random")
                lines.append(f"{indent}{res} = random.{op}({args})")
            elif t == "Lambda":
                name, params, body = p.get("name", "f"), p.get("params", "x"), p.get("body", "x")
                lines.append(f"{indent}{name} = lambda {params}: {body}")
            elif t == "List Comprehension":
                res, expr, var, it, cond = (
                    p.get("result", "s"),
                    p.get("expression", "x"),
                    p.get("variable", "x"),
                    p.get("iterable", "liste"),
                    p.get("condition", ""),
                )
                cond_part = f" if {cond}" if cond else ""
                lines.append(f"{indent}{res} = [{expr} for {var} in {it}{cond_part}]")
            elif t == "Assert":
                cond, msg = p.get("condition", "True"), p.get("message", "Assertion failed")
                lines.append(f"{indent}assert {cond}, '{msg}'")
            elif t == "Import":
                mod, alias, frm = p.get("module", "math"), p.get("alias", ""), p.get("from_import", "")
                if frm:
                    lines.append(f"{indent}from {mod} import {frm}")
                elif alias:
                    lines.append(f"{indent}import {mod} as {alias}")
                else:
                    lines.append(f"{indent}import {mod}")
            elif t == "File Read":
                fp, var, mode = p.get("filepath", "dosya.txt"), p.get("variable", "icerik"), p.get("mode", "all")
                read_fn = {"all": "read()", "lines": "readlines()", "line": "readline()"}.get(mode, "read()")
                lines.append(f"{indent}with open('{fp}', 'r', encoding='utf-8') as f:")
                lines.append(f"{indent}    {var} = f.{read_fn}")
            elif t == "File Write":
                fp, expr, mode = p.get("filepath", "cikti.txt"), p.get("expression", ""), p.get("mode", "w")
                lines.append(f"{indent}with open('{fp}', '{mode}', encoding='utf-8') as f:")
                lines.append(f"{indent}    f.write(str({expr}))")
            elif t == "Delay":
                lines.append(f"{indent}import time")
                lines.append(f"{indent}time.sleep({p.get('seconds', '1')})")
            elif t == "Function":
                fn, params = p.get("function_name", "my_func"), p.get("parameters", "")
                lines.append("")
                lines.append(f"def {fn}({params}):")
                lines.append("    pass  # function body")
                lines.append("")
            elif t == "Return":
                lines.append(f"{indent}return {p.get('expression', '')}")
            elif t == "Stop":
                msg = p.get("message", "")
                if msg:
                    lines.append(f"{indent}print('{msg}')")
                lines.append(f"{indent}return")
            elif t == "Comment":
                for line in p.get("text", "").split("\n"):
                    lines.append(f"{indent}# {line}")

        lines.append("")
        lines.append("")
        lines.append("if __name__ == '__main__':")
        lines.append("    main()")
        return "\n".join(lines)

    # ── JAVA ─────────────────────────────────────────────────────────

    def _gen_java(self, nodes) -> str:
        lines = [
            "// FlowPy Tarafından Üretilen Java Kodu",
            "import java.util.Scanner;",
            "import java.util.*;",
            "",
            "public class FlowProgram {",
            "    public static void main(String[] args) {",
            "        Scanner scanner = new Scanner(System.in);",
        ]
        ind = "        "

        for node in nodes:
            t, p = node.title, node.properties
            if t == "Variable":
                name, val, typ = p.get("name", "x"), p.get("value", "0"), p.get("type", "auto")
                java_type = {"int": "int", "float": "double", "str": "String", "bool": "boolean", "auto": "var"}.get(
                    typ, "var"
                )
                lines.append(f"{ind}{java_type} {name} = {val};")
            elif t == "Process":
                for line in p.get("code", "").strip().split("\n"):
                    if line.strip():
                        lines.append(f"{ind}{line.strip()};")
            elif t == "Print":
                lines.append(f"{ind}System.out.println({p.get('expression', '')});")
            elif t == "Math":
                r, a, op, b = (
                    p.get("result", "r"),
                    p.get("operand_a", "a"),
                    p.get("operator", "+"),
                    p.get("operand_b", "b"),
                )
                lines.append(f"{ind}var {r} = {a} {op} {b};")
            elif t == "Input":
                var, typ = p.get("variable", "x"), p.get("input_type", "str")
                if typ == "int":
                    lines.append(f"{ind}int {var} = scanner.nextInt();")
                elif typ == "float":
                    lines.append(f"{ind}double {var} = scanner.nextDouble();")
                else:
                    lines.append(f"{ind}String {var} = scanner.nextLine();")
            elif t == "Output":
                lines.append(f"{ind}System.out.println({p.get('expression', '')});")
            elif t == "Decision":
                lines.append(f"{ind}if ({p.get('condition', 'true')}) {{")
                lines.append(f"{ind}    // True branch")
                lines.append(f"{ind}}} else {{")
                lines.append(f"{ind}    // False branch")
                lines.append(f"{ind}}}")
            elif t == "If Elif Else":
                lines.append(f"{ind}if ({p.get('condition_if', 'true')}) {{")
                lines.append(f"{ind}    // if branch")
                lines.append(f"{ind}}} else if ({p.get('condition_elif', 'false')}) {{")
                lines.append(f"{ind}    // elif branch")
                lines.append(f"{ind}}} else {{")
                lines.append(f"{ind}    // else branch")
                lines.append(f"{ind}}}")
            elif t == "While":
                lines.append(f"{ind}while ({p.get('condition', 'true')}) {{")
                lines.append(f"{ind}    // loop body")
                lines.append(f"{ind}}}")
            elif t == "For":
                v, s, e, stp = (
                    p.get("variable", "i"),
                    p.get("start", "0"),
                    p.get("end", "10"),
                    p.get("step", "1"),
                )
                lines.append(f"{ind}for (int {v} = {s}; {v} < {e}; {v} += {stp}) {{")
                lines.append(f"{ind}    // loop body")
                lines.append(f"{ind}}}")
            elif t == "Break":
                lines.append(f"{ind}break;")
            elif t == "Continue":
                lines.append(f"{ind}continue;")
            elif t == "Swap":
                a, b = p.get("var_a", "a"), p.get("var_b", "b")
                lines.append(f"{ind}var _tmp = {a}; {a} = {b}; {b} = _tmp;")
            elif t == "Accumulate":
                acc, op, val = p.get("accumulator", "sum"), p.get("operation", "+="), p.get("value", "x")
                lines.append(f"{ind}{acc} {op} {val};")
            elif t == "Assert":
                lines.append(f'{ind}assert {p.get("condition", "true")} : "{p.get("message", "")}";')
            elif t == "Import":
                lines.insert(1, f'import {p.get("module", "java.util.*")};')
            elif t == "Return":
                lines.append(f"{ind}return {p.get('expression', '')};")
            elif t == "Comment":
                for line in p.get("text", "").split("\n"):
                    lines.append(f"{ind}// {line}")
            elif t == "Stop":
                msg = p.get("message", "")
                if msg:
                    lines.append(f'{ind}System.out.println("{msg}");')
                lines.append(f"{ind}return;")

        lines.append("    }")
        lines.append("}")
        return "\n".join(lines)

    # ── C ────────────────────────────────────────────────────────────

    def _gen_c(self, nodes) -> str:
        lines = [
            "/* FlowPy Tarafından Üretilen C Kodu */",
            "#include <stdio.h>",
            "#include <stdlib.h>",
            "#include <string.h>",
            "",
            "int main() {",
        ]
        ind = "    "

        for node in nodes:
            t, p = node.title, node.properties
            if t == "Variable":
                name, val, typ = p.get("name", "x"), p.get("value", "0"), p.get("type", "auto")
                c_type = {"int": "int", "float": "float", "str": "char*", "bool": "int", "auto": "int"}.get(typ, "int")
                lines.append(f"{ind}{c_type} {name} = {val};")
            elif t == "Print":
                lines.append(f'{ind}printf("%s\\n", {p.get("expression", "")});')
            elif t == "Math":
                r, a, op, b = (
                    p.get("result", "r"),
                    p.get("operand_a", "a"),
                    p.get("operator", "+"),
                    p.get("operand_b", "b"),
                )
                lines.append(f"{ind}int {r} = {a} {op} {b};")
            elif t == "Input":
                var, typ = p.get("variable", "x"), p.get("input_type", "int")
                lines.append(f'{ind}printf("{p.get("prompt", "Girin: ")}\\n");')
                if typ == "str":
                    lines.append(f'{ind}char {var}[256]; scanf("%s", {var});')
                else:
                    fmt_c = "%d" if typ == "int" else "%f"
                    c_type = "int" if typ == "int" else "float"
                    lines.append(f'{ind}{c_type} {var}; scanf("{fmt_c}", &{var});')
            elif t == "Output":
                lines.append(f'{ind}printf("%d\\n", {p.get("expression", "0")});')
            elif t == "Decision":
                lines.append(f"{ind}if ({p.get('condition', '1')}) {{")
                lines.append(f"{ind}    /* True */")
                lines.append(f"{ind}}} else {{")
                lines.append(f"{ind}    /* False */")
                lines.append(f"{ind}}}")
            elif t == "If Elif Else":
                lines.append(f"{ind}if ({p.get('condition_if', '1')}) {{")
                lines.append(f"{ind}    /* if */")
                lines.append(f"{ind}}} else if ({p.get('condition_elif', '0')}) {{")
                lines.append(f"{ind}    /* elif */")
                lines.append(f"{ind}}} else {{")
                lines.append(f"{ind}    /* else */")
                lines.append(f"{ind}}}")
            elif t == "While":
                lines.append(f"{ind}while ({p.get('condition', '1')}) {{")
                lines.append(f"{ind}    /* loop body */")
                lines.append(f"{ind}}}")
            elif t == "For":
                v, s, e, stp = (
                    p.get("variable", "i"),
                    p.get("start", "0"),
                    p.get("end", "10"),
                    p.get("step", "1"),
                )
                lines.append(f"{ind}for (int {v} = {s}; {v} < {e}; {v} += {stp}) {{")
                lines.append(f"{ind}    /* loop body */")
                lines.append(f"{ind}}}")
            elif t == "Break":
                lines.append(f"{ind}break;")
            elif t == "Continue":
                lines.append(f"{ind}continue;")
            elif t == "Swap":
                a, b = p.get("var_a", "a"), p.get("var_b", "b")
                lines.append(f"{ind}int _tmp = {a}; {a} = {b}; {b} = _tmp;")
            elif t == "Accumulate":
                acc, op, val = p.get("accumulator", "sum"), p.get("operation", "+="), p.get("value", "x")
                lines.append(f"{ind}{acc} {op} {val};")
            elif t == "Return":
                lines.append(f"{ind}return {p.get('expression', '0')};")
            elif t == "Comment":
                for line in p.get("text", "").split("\n"):
                    lines.append(f"{ind}/* {line} */")
            elif t == "Stop":
                msg = p.get("message", "")
                if msg:
                    lines.append(f'{ind}printf("{msg}\\n");')
                lines.append(f"{ind}return 0;")

        lines.append(f"{ind}return 0;")
        lines.append("}")
        return "\n".join(lines)

    # ── C++ ──────────────────────────────────────────────────────────

    def _gen_cpp(self, nodes) -> str:
        lines = [
            "// FlowPy Tarafından Üretilen C++ Kodu",
            "#include <iostream>",
            "#include <vector>",
            "#include <algorithm>",
            "#include <string>",
            "using namespace std;",
            "",
            "int main() {",
        ]
        ind = "    "

        for node in nodes:
            t, p = node.title, node.properties
            if t == "Variable":
                name, val, typ = p.get("name", "x"), p.get("value", "0"), p.get("type", "auto")
                cpp_type = {"int": "int", "float": "double", "str": "string", "bool": "bool", "auto": "auto"}.get(
                    typ, "auto"
                )
                lines.append(f"{ind}{cpp_type} {name} = {val};")
            elif t == "Print":
                lines.append(f'{ind}cout << {p.get("expression", "")} << endl;')
            elif t == "Output":
                lines.append(f'{ind}cout << {p.get("expression", "")} << endl;')
            elif t == "Math":
                r, a, op, b = (
                    p.get("result", "r"),
                    p.get("operand_a", "a"),
                    p.get("operator", "+"),
                    p.get("operand_b", "b"),
                )
                lines.append(f"{ind}auto {r} = {a} {op} {b};")
            elif t == "Input":
                var, typ = p.get("variable", "x"), p.get("input_type", "int")
                cpp_type = {"int": "int", "float": "double", "str": "string", "auto": "int"}.get(typ, "int")
                lines.append(f'{ind}cout << "{p.get("prompt", "Girin: ")}" << endl;')
                lines.append(f"{ind}{cpp_type} {var}; cin >> {var};")
            elif t == "Decision":
                lines.append(f"{ind}if ({p.get('condition', 'true')}) {{")
                lines.append(f"{ind}    // True")
                lines.append(f"{ind}}} else {{")
                lines.append(f"{ind}    // False")
                lines.append(f"{ind}}}")
            elif t == "While":
                lines.append(f"{ind}while ({p.get('condition', 'true')}) {{")
                lines.append(f"{ind}    // loop")
                lines.append(f"{ind}}}")
            elif t == "For":
                v, s, e, stp = (
                    p.get("variable", "i"),
                    p.get("start", "0"),
                    p.get("end", "10"),
                    p.get("step", "1"),
                )
                lines.append(f"{ind}for (int {v} = {s}; {v} < {e}; {v} += {stp}) {{")
                lines.append(f"{ind}    // loop body")
                lines.append(f"{ind}}}")
            elif t == "Break":
                lines.append(f"{ind}break;")
            elif t == "Continue":
                lines.append(f"{ind}continue;")
            elif t == "Swap":
                a, b = p.get("var_a", "a"), p.get("var_b", "b")
                lines.append(f"{ind}swap({a}, {b});")
            elif t == "Sort":
                lv = p.get("list_var", "v")
                rev = p.get("reverse", "False") == "True"
                if rev:
                    lines.append(f"{ind}sort({lv}.rbegin(), {lv}.rend());")
                else:
                    lines.append(f"{ind}sort({lv}.begin(), {lv}.end());")
            elif t == "Return":
                lines.append(f"{ind}return {p.get('expression', '0')};")
            elif t == "Comment":
                for line in p.get("text", "").split("\n"):
                    lines.append(f"{ind}// {line}")

        lines.append(f"{ind}return 0;")
        lines.append("}")
        return "\n".join(lines)

    # ── JAVASCRIPT ───────────────────────────────────────────────────

    def _gen_js(self, nodes) -> str:
        lines = ["// FlowPy Tarafından Üretilen JavaScript Kodu", "", "function main() {"]
        ind = "    "

        for node in nodes:
            t, p = node.title, node.properties
            if t == "Variable":
                name, val = p.get("name", "x"), p.get("value", "0")
                lines.append(f"{ind}let {name} = {val};")
            elif t == "Process":
                for line in p.get("code", "").strip().split("\n"):
                    if line.strip():
                        lines.append(f"{ind}{line.strip()}")
            elif t == "Print":
                lines.append(f"{ind}console.log({p.get('expression', '')});")
            elif t == "Output":
                lines.append(f"{ind}console.log({p.get('expression', '')});")
            elif t == "Math":
                r, a, op, b = (
                    p.get("result", "r"),
                    p.get("operand_a", "a"),
                    p.get("operator", "+"),
                    p.get("operand_b", "b"),
                )
                lines.append(f"{ind}let {r} = {a} {op} {b};")
            elif t == "Input":
                var, prompt = p.get("variable", "x"), p.get("prompt", "Girin:")
                lines.append(f"{ind}let {var} = prompt('{prompt}');")
            elif t == "Decision":
                lines.append(f"{ind}if ({p.get('condition', 'true')}) {{")
                lines.append(f"{ind}    // True branch")
                lines.append(f"{ind}}} else {{")
                lines.append(f"{ind}    // False branch")
                lines.append(f"{ind}}}")
            elif t == "While":
                lines.append(f"{ind}while ({p.get('condition', 'true')}) {{")
                lines.append(f"{ind}    // loop body")
                lines.append(f"{ind}}}")
            elif t == "For":
                v, s, e, stp = (
                    p.get("variable", "i"),
                    p.get("start", "0"),
                    p.get("end", "10"),
                    p.get("step", "1"),
                )
                lines.append(f"{ind}for (let {v} = {s}; {v} < {e}; {v} += {stp}) {{")
                lines.append(f"{ind}    // loop body")
                lines.append(f"{ind}}}")
            elif t == "Break":
                lines.append(f"{ind}break;")
            elif t == "Continue":
                lines.append(f"{ind}continue;")
            elif t == "Swap":
                a, b = p.get("var_a", "a"), p.get("var_b", "b")
                lines.append(f"{ind}[{a}, {b}] = [{b}, {a}];")
            elif t == "Lambda":
                name, params, body = p.get("name", "f"), p.get("params", "x"), p.get("body", "x")
                lines.append(f"{ind}const {name} = ({params}) => {body};")
            elif t == "Assert":
                lines.append(f"{ind}console.assert({p.get('condition', 'true')}, '{p.get('message', '')}');")
            elif t == "Return":
                lines.append(f"{ind}return {p.get('expression', '')};")
            elif t == "Comment":
                for line in p.get("text", "").split("\n"):
                    lines.append(f"{ind}// {line}")

        lines.append("}")
        lines.append("")
        lines.append("main();")
        return "\n".join(lines)

    # ── PSEUDOCODE ───────────────────────────────────────────────────

    def _gen_pseudo(self, nodes) -> str:
        lines = ["// FlowPy — Pseudocode", ""]
        lines.append("BAŞLA")

        for node in nodes:
            t, p = node.title, node.properties
            if t == "Start":
                vars_code = p.get("variables", "").strip()
                if vars_code:
                    for v in vars_code.split("\n"):
                        lines.append(f"  TANIMLA {v.strip()}")
            elif t == "Variable":
                lines.append(f"  TANIMLA {p.get('name', 'x')} ← {p.get('value', '0')}")
            elif t == "Process":
                for line in p.get("code", "").strip().split("\n"):
                    if line.strip():
                        lines.append(f"  İŞLEM: {line.strip()}")
            elif t == "Print":
                lines.append(f"  YAZDIR {p.get('expression', '')}")
            elif t == "Math":
                r, a, op, b = (
                    p.get("result", "r"),
                    p.get("operand_a", "a"),
                    p.get("operator", "+"),
                    p.get("operand_b", "b"),
                )
                lines.append(f"  {r} ← {a} {op} {b}")
            elif t == "Input":
                lines.append(f"  OKU {p.get('variable', 'x')} ({p.get('prompt', '')})")
            elif t == "Output":
                lines.append(f"  ÇIKTI: {p.get('expression', '')}")
            elif t == "Decision":
                lines.append(f"  EĞER {p.get('condition', '')} İSE")
                lines.append("    // doğru yol")
                lines.append("  DEĞİLSE")
                lines.append("    // yanlış yol")
                lines.append("  EĞER SONU")
            elif t == "If Elif Else":
                lines.append(f"  EĞER {p.get('condition_if', '')} İSE")
                lines.append("    // if yolu")
                lines.append(f"  YA DA EĞER {p.get('condition_elif', '')} İSE")
                lines.append("    // elif yolu")
                lines.append("  DEĞİLSE")
                lines.append("    // else yolu")
                lines.append("  EĞER SONU")
            elif t == "While":
                lines.append(f"  DÖNGÜ ({p.get('condition', '')} olduğu sürece)")
                lines.append("    // döngü gövdesi")
                lines.append("  DÖNGÜ SONU")
            elif t == "For":
                v, s, e, stp = (
                    p.get("variable", "i"),
                    p.get("start", "0"),
                    p.get("end", "10"),
                    p.get("step", "1"),
                )
                lines.append(f"  {v} = {s}'DEN {e}'E {stp} ADIMLA")
                lines.append("    // döngü gövdesi")
                lines.append("  DÖNGÜ SONU")
            elif t == "Break":
                lines.append("  DÖNGÜDEN ÇIK")
            elif t == "Continue":
                lines.append("  BU ADIMI ATLA")
            elif t == "Swap":
                a, b = p.get("var_a", "a"), p.get("var_b", "b")
                lines.append(f"  GEÇİCİ ← {a}; {a} ← {b}; {b} ← GEÇİCİ")
            elif t == "Accumulate":
                acc, op, val = p.get("accumulator", "toplam"), p.get("operation", "+="), p.get("value", "x")
                lines.append(f"  {acc} ← {acc} {op.replace('=', '')} {val}")
            elif t == "Sort":
                lines.append(f"  SIRALA {p.get('list_var', 'liste')}")
            elif t == "Search":
                lv, tgt = p.get("list_var", "liste"), p.get("target", "hedef")
                lines.append(f"  ARA {tgt} içinde {lv}")
            elif t == "Lambda":
                lines.append(f"  FONKSİYON {p.get('name', 'f')}({p.get('params', 'x')}) = {p.get('body', 'x')}")
            elif t == "Return":
                lines.append(f"  DÖNÜŞ {p.get('expression', '')}")
            elif t == "Function":
                fn, params = p.get("function_name", "my_func"), p.get("parameters", "")
                lines.append(f"  FONKSİYON {fn}({params}):")
                lines.append("    // gövde")
                lines.append("  FONKSİYON SONU")
            elif t == "Stop":
                msg = p.get("message", "")
                if msg:
                    lines.append(f"  YAZDIR '{msg}'")
                lines.append("  DUR")
            elif t == "Comment":
                for line in p.get("text", "").split("\n"):
                    lines.append(f"  // {line}")

        lines.append("BİTİR")
        return "\n".join(lines)
