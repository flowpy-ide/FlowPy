# core/generator.py
# ──────────────────────────────────────────────────────────────────────
# CodeGenerator : FlowPy sahnesindeki (NodeRegistry) grafik formunu
#                 okuyarak Pseudocode, Python, C ve Java çıktıları üretir.
#                 DFS tabanlı basit bir AST (Abstract Syntax Tree) çıkarımı yapar.
# ──────────────────────────────────────────────────────────────────────

from core.registry import NodeRegistry

class CodeGenerator:
    """Akış modelini okuyarak kod üreten ana motor."""

    def __init__(self, registry: NodeRegistry):
        self.registry = registry
        self.var_types = {} # {var_name: type_str} where type_str is 'int', 'double', or 'string'

    def _infer_type(self, value: str):
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            return "string"
        if value.replace('.', '', 1).isdigit():
            if "." in value:
                return "double"
            return "int"
        return "double" # Default fallback

    def _translate_cond(self, cond: str, lang: str):
        cond = cond.strip()
        if cond in self.var_types:
            vtype = self.var_types[cond]
            if lang == "c":
                if vtype == "string":
                    return f"({cond} != NULL && strlen({cond}) > 0)"
                else:
                    return f"({cond} != 0)"
            elif lang == "java":
                if vtype == "string":
                    return f"({cond} != null && !{cond}.isEmpty())"
                else:
                    return f"({cond} != 0)"
        # Default translation
        if lang == "java":
            if cond.lower() == "true": return "true"
            if cond.lower() == "false": return "false"
        return cond

    def _python_input_line(self, node, indent: str) -> str:
        """INPUT düğümü için input_type'a göre Python satırı üretir."""
        var_name = node.properties.get("variable", "user_in").strip()
        prompt = node.properties.get("prompt", "").strip()
        input_type = node.properties.get("input_type", "auto").strip()
        inner = f"input('{prompt} ')"
        if input_type == "int":
            expr = f"int({inner})"
        elif input_type == "float":
            expr = f"float({inner})"
        elif input_type == "str":
            expr = inner
        else:
            expr = inner
        return f"{indent}{var_name} = {expr}\n"

    def _get_start_node(self):
        nodes = self.registry.get_all_nodes()
        for n in nodes.values():
            if getattr(n, "title", "") == "Start":
                return n
        return None

    def _get_next_node(self, current_node, port_index: int = 0):
        if port_index >= len(current_node.output_ports):
            return None
        source_port = current_node.output_ports[port_index]
        for edge in current_node.edges:
            if getattr(edge, 'source_port', None) is source_port:
                return edge.dest_node
        return None

    # ── Ortak Ağaç Gezinme (Tree Traversal) ──────────────────────────

    def generate(self, language: str) -> str:
        """Belirtilen dile göre kod / pseudocode üretir."""
        start_node = self._get_start_node()
        if not start_node:
            return "/* HATA: Akışta 'Start' düğümü bulunamadı! */"
        
        visited = set()
        
        if language.lower() == "python":
            return self._generate_python(start_node, visited, indent_level=0)
        elif language.lower() == "pseudocode":
            return self._generate_pseudo(start_node, visited, indent_level=0)
        elif language.lower() == "c":
            return self._generate_c(start_node, visited, indent_level=0)
        elif language.lower() == "java":
            return self._generate_java(start_node, visited, indent_level=0)
        else:
            return f"/* Desteklenmeyen dil: {language} */"

    # ── P S E U D O C O D E ──────────────────────────────────────────

    def _generate_pseudo(self, node, visited: set, indent_level: int) -> str:
        if not node or id(node) in visited:
            return ""
        
        visited.add(id(node))
        indent = "  " * indent_level
        code = ""
        title = getattr(node, "title", "?")

        if title == "Start":
            code += f"{indent}BAŞLA\n"
            vars_str = node.properties.get("variables", "").strip()
            if vars_str:
                for line in vars_str.split("\n"):
                    code += f"{indent}  Ata: {line}\n"
            code += self._generate_pseudo(self._get_next_node(node, 0), visited, indent_level)
            code += f"{indent}BİTİR\n"

        elif title == "Process":
            process_code = node.properties.get("code", "İşlem yap").strip()
            code += f"{indent}İŞLEM YAP: {process_code}\n"
            code += self._generate_pseudo(self._get_next_node(node, 0), visited, indent_level)

        elif title == "Input":
            var_name = node.properties.get("variable", "X").strip()
            prompt = node.properties.get("prompt", "Girdi girin:").strip()
            code += f"{indent}KULLANICIDAN OKU ({prompt}) -> {var_name}\n"
            code += self._generate_pseudo(self._get_next_node(node, 0), visited, indent_level)

        elif title == "Output":
            expr = node.properties.get("expression", "Sonuç").strip()
            code += f"{indent}EKRANA YAZDIR: {expr}\n"
            code += self._generate_pseudo(self._get_next_node(node, 0), visited, indent_level)

        elif title == "Decision":
            cond = node.properties.get("condition", "Koşul").strip()
            code += f"{indent}EĞER ( {cond} ) İSE:\n"
            
            # True dalı (port 0)
            true_node = self._get_next_node(node, 0)
            if true_node:
                code += self._generate_pseudo(true_node, set(visited), indent_level + 1)
            else:
                code += f"{indent}  (Boş)\n"

            # False dalı (port 1)
            false_node = self._get_next_node(node, 1)
            if false_node:
                code += f"{indent}DEĞİLSE:\n"
                code += self._generate_pseudo(false_node, set(visited), indent_level + 1)
                
            code += f"{indent}EĞER BİTİR\n"
            
            # Dal sonu birleştirmesi Pseudocode'da karmaşık olmasın diye 
            # while ve fonksiyonsuz varsayalım. Asıl kodda DFS devam eder.

        elif title == "While":
            cond = node.properties.get("condition", "Koşul").strip()
            code += f"{indent}DÖNGÜ SÜRDÜKÇE ( {cond} ):\n"
            # Loop dalı (port 0)
            loop_node = self._get_next_node(node, 0)
            if loop_node:
                code += self._generate_pseudo(loop_node, set(visited), indent_level + 1)
            
            code += f"{indent}DÖNGÜ BİTİR\n"
            # Exit dalı (port 1)
            exit_node = self._get_next_node(node, 1)
            if exit_node:
                code += self._generate_pseudo(exit_node, visited, indent_level)

        elif title == "For":
            var_name = node.properties.get("variable", "i")
            start = node.properties.get("start", "0")
            end = node.properties.get("end", "10")
            step = node.properties.get("step", "1")
            
            code += f"{indent}SAYAÇ DÖNGÜSÜ: {var_name} = {start}'dan {end}'a kadar ({step} artırarak):\n"
            # Loop dalı
            loop_node = self._get_next_node(node, 0)
            if loop_node:
                code += self._generate_pseudo(loop_node, set(visited), indent_level + 1)
                
            code += f"{indent}SAYAÇ BİTİR\n"
            exit_node = self._get_next_node(node, 1)
            if exit_node:
                code += self._generate_pseudo(exit_node, visited, indent_level)
                
        elif title == "Function":
            func_name = node.properties.get("function_name", "Fonksiyon")
            params = node.properties.get("parameters", "")
            code += f"{indent}FONKSİYON TANIMLA: {func_name}({params})\n"
            code += self._generate_pseudo(self._get_next_node(node, 0), visited, indent_level + 1)
            
        elif title == "Return":
            expr = node.properties.get("expression", "Değer")
            code += f"{indent}GERİ DÖNDÜR: {expr}\n"

        return code

    # ── P Y T H O N ──────────────────────────────────────────────────

    def _generate_python(self, node, visited: set, indent_level: int) -> str:
        if not node or id(node) in visited:
            return ""
        
        visited.add(id(node))
        indent = "    " * indent_level
        code = ""
        title = getattr(node, "title", "?")

        if title == "Start":
            code += "# FlowPy Tarafından Üretilen Python Kodu\n\n"
            code += "def main():\n"
            
            vars_str = node.properties.get("variables", "").strip()
            indent_inner = "    "
            if vars_str:
                for line in vars_str.split("\n"):
                    code += f"{indent_inner}{line}\n"
            
            inner_code = self._generate_python(self._get_next_node(node, 0), visited, 1)
            if not inner_code and not vars_str:
                code += f"{indent_inner}pass\n"
            else:
                code += inner_code
                
            code += "\nif __name__ == '__main__':\n    main()\n"

        elif title == "Process":
            process_code = node.properties.get("code", "").strip()
            if process_code:
                for line in process_code.split("\n"):
                    code += f"{indent}{line}\n"
            code += self._generate_python(self._get_next_node(node, 0), visited, indent_level)

        elif title == "Input":
            code += self._python_input_line(node, indent)
            code += self._generate_python(self._get_next_node(node, 0), visited, indent_level)

        elif title == "Output":
            expr = node.properties.get("expression", "''").strip()
            code += f"{indent}print({expr})\n"
            code += self._generate_python(self._get_next_node(node, 0), visited, indent_level)

        elif title == "Decision":
            cond = node.properties.get("condition", "True").strip()
            code += f"{indent}if {cond}:\n"
            
            true_node = self._get_next_node(node, 0)
            if true_node:
                code += self._generate_python(true_node, set(visited), indent_level + 1)
            else:
                code += f"{indent}    pass\n"

            false_node = self._get_next_node(node, 1)
            if false_node:
                code += f"{indent}else:\n"
                code += self._generate_python(false_node, set(visited), indent_level + 1)

        elif title == "While":
            cond = node.properties.get("condition", "True").strip()
            code += f"{indent}while {cond}:\n"
            
            loop_node = self._get_next_node(node, 0)
            if loop_node:
                code += self._generate_python(loop_node, set(visited), indent_level + 1)
            else:
                code += f"{indent}    pass\n"
                
            exit_node = self._get_next_node(node, 1)
            if exit_node:
                code += self._generate_python(exit_node, visited, indent_level)

        elif title == "For":
            var_name = node.properties.get("variable", "i")
            start = node.properties.get("start", "0")
            end = node.properties.get("end", "10")
            step = node.properties.get("step", "1")
            
            code += f"{indent}for {var_name} in range({start}, {end}, {step}):\n"
            loop_node = self._get_next_node(node, 0)
            if loop_node:
                code += self._generate_python(loop_node, set(visited), indent_level + 1)
            else:
                code += f"{indent}    pass\n"
                
            exit_node = self._get_next_node(node, 1)
            if exit_node:
                code += self._generate_python(exit_node, visited, indent_level)

        elif title == "Function":
            func_name = getattr(node, "function_name", node.properties.get("function_name", "my_func"))
            params = node.properties.get("parameters", "")
            code += f"\n{indent}def {func_name}({params}):\n"
            inner = self._generate_python(self._get_next_node(node, 0), visited, indent_level + 1)
            if not inner:
                code += f"{indent}    pass\n"
            else:
                code += inner
                
        elif title == "Return":
            expr = node.properties.get("expression", "None")
            code += f"{indent}return {expr}\n"
            
        return code

    # ── C / J A V A (Doğrudan AST Dönüşümü) ──────────────

    def _generate_c(self, node, visited: set, indent_level: int) -> str:
        if not node or id(node) in visited:
            return ""
        
        visited.add(id(node))
        indent = "    " * indent_level
        code = ""
        title = getattr(node, "title", "?")

        if title == "Start":
            self.var_types = {}
            code += "/* FlowPy Generated C Code */\n\n"
            code += "#include <stdio.h>\n"
            code += "#include <stdlib.h>\n"
            code += "#include <string.h>\n"
            code += "#include <stdbool.h>\n\n"
            code += "int main() {\n"
            
            vars_str = node.properties.get("variables", "").strip()
            indent_inner = "    "
            if vars_str:
                for line in vars_str.split("\n"):
                    if "=" in line:
                        parts = line.split("=")
                        var_name = parts[0].strip()
                        val = parts[1].strip()
                        vtype = self._infer_type(val)
                        self.var_types[var_name] = vtype
                        
                        if vtype == "string":
                            code += f"{indent_inner}char* {var_name} = {val};\n"
                        elif vtype == "double":
                            code += f"{indent_inner}double {var_name} = {val};\n"
                        else:
                            code += f"{indent_inner}int {var_name} = {val};\n"
                    else:
                        code += f"{indent_inner}// {line}\n"
            
            inner_code = self._generate_c(self._get_next_node(node, 0), visited, 1)
            code += inner_code
                
            code += f"\n{indent_inner}return 0;\n}}\n"

        elif title == "Process":
            process_code = node.properties.get("code", "").strip()
            if process_code:
                for line in process_code.split("\n"):
                    if "=" in line and "==" not in line:
                        parts = line.split("=")
                        var_name = parts[0].strip()
                        val = parts[1].strip()
                        if var_name not in self.var_types:
                            vtype = self._infer_type(val)
                            self.var_types[var_name] = vtype
                            decl = "char* " if vtype == "string" else ("double " if vtype == "double" else "int ")
                            code += f"{indent}{decl}{line};\n"
                        else:
                            code += f"{indent}{line};\n"
                    else:
                        code += f"{indent}{line};\n"
            code += self._generate_c(self._get_next_node(node, 0), visited, indent_level)

        elif title == "Input":
            var_name = node.properties.get("variable", "user_in").strip()
            prompt = node.properties.get("prompt", "").strip()
            if var_name not in self.var_types:
                self.var_types[var_name] = "double" # Assume double for input
                code += f"{indent}double {var_name};\n"
            code += f"{indent}printf(\"{prompt} \");\n"
            code += f"{indent}scanf(\"%lf\", &{var_name});\n"
            code += self._generate_c(self._get_next_node(node, 0), visited, indent_level)

        elif title == "Output":
            expr = node.properties.get("expression", "''").strip()
            if expr.startswith("'") or expr.startswith('"'):
                code += f"{indent}printf({expr});\n{indent}printf(\"\\n\");\n"
            elif expr in self.var_types:
                vtype = self.var_types[expr]
                if vtype == "string":
                    code += f"{indent}printf(\"%s\\n\", {expr});\n"
                elif vtype == "int":
                    code += f"{indent}printf(\"%d\\n\", {expr});\n"
                else:
                    code += f"{indent}printf(\"%f\\n\", {expr});\n"
            else:
                code += f"{indent}printf(\"%f\\n\", (double)({expr}));\n"
            code += self._generate_c(self._get_next_node(node, 0), visited, indent_level)

        elif title == "Decision":
            cond = node.properties.get("condition", "1").strip()
            cond = self._translate_cond(cond, "c")
            code += f"{indent}if ({cond}) {{\n"
            
            true_node = self._get_next_node(node, 0)
            if true_node:
                code += self._generate_c(true_node, set(visited), indent_level + 1)

            false_node = self._get_next_node(node, 1)
            if false_node:
                code += f"{indent}}} else {{\n"
                code += self._generate_c(false_node, set(visited), indent_level + 1)
                
            code += f"{indent}}}\n"

        elif title == "While":
            cond = node.properties.get("condition", "1").strip()
            cond = self._translate_cond(cond, "c")
            code += f"{indent}while ({cond}) {{\n"
            
            loop_node = self._get_next_node(node, 0)
            if loop_node:
                code += self._generate_c(loop_node, set(visited), indent_level + 1)
                
            code += f"{indent}}}\n"
            exit_node = self._get_next_node(node, 1)
            if exit_node:
                code += self._generate_c(exit_node, visited, indent_level)

        elif title == "For":
            var_name = node.properties.get("variable", "i")
            start = node.properties.get("start", "0")
            end = node.properties.get("end", "10")
            step = node.properties.get("step", "1")
            
            code += f"{indent}for (int {var_name} = {start}; {var_name} < {end}; {var_name} += {step}) {{\n"
            loop_node = self._get_next_node(node, 0)
            if loop_node:
                code += self._generate_c(loop_node, set(visited), indent_level + 1)
                
            code += f"{indent}}}\n"
            exit_node = self._get_next_node(node, 1)
            if exit_node:
                code += self._generate_c(exit_node, visited, indent_level)

        elif title == "Function":
            func_name = getattr(node, "function_name", node.properties.get("function_name", "my_func"))
            params = node.properties.get("parameters", "")
            c_params = [f"double {p.strip()}" for p in params.split(",") if p.strip()]
            param_str = ", ".join(c_params)
            
            code += f"\n{indent}double {func_name}({param_str}) {{\n"
            inner = self._generate_c(self._get_next_node(node, 0), visited, indent_level + 1)
            code += inner
            code += f"{indent}}}\n"
                
        elif title == "Return":
            expr = node.properties.get("expression", "0")
            code += f"{indent}return {expr};\n"
            
        return code

    def _generate_java(self, node, visited: set, indent_level: int) -> str:
        if not node or id(node) in visited:
            return ""
        
        visited.add(id(node))
        indent = "    " * indent_level
        code = ""
        title = getattr(node, "title", "?")

        if title == "Start":
            self.var_types = {}
            code += "/* FlowPy Generated Java Code */\n\n"
            code += "import java.util.Scanner;\n\n"
            code += "public class FlowPyExport {\n"
            indent_inner = "    "
            code += f"{indent_inner}public static void main(String[] args) {{\n"
            code += f"{indent_inner}    Scanner scanner = new Scanner(System.in);\n"
            
            vars_str = node.properties.get("variables", "").strip()
            if vars_str:
                for line in vars_str.split("\n"):
                    if "=" in line:
                        parts = line.split("=")
                        var_name = parts[0].strip()
                        val = parts[1].strip()
                        vtype = self._infer_type(val)
                        self.var_types[var_name] = vtype
                        
                        if vtype == "string":
                            code += f"{indent_inner}    String {var_name} = {val};\n"
                        elif vtype == "double":
                            code += f"{indent_inner}    double {var_name} = {val};\n"
                        else:
                            code += f"{indent_inner}    int {var_name} = {val};\n"
                    else:
                        code += f"{indent_inner}    // {line}\n"
            
            inner_code = self._generate_java(self._get_next_node(node, 0), visited, 2)
            code += inner_code
                
            code += f"{indent_inner}}}\n}}\n"

        elif title == "Process":
            process_code = node.properties.get("code", "").strip()
            if process_code:
                for line in process_code.split("\n"):
                    if "=" in line and "==" not in line:
                        parts = line.split("=")
                        var_name = parts[0].strip()
                        val = parts[1].strip()
                        if var_name not in self.var_types:
                            vtype = self._infer_type(val)
                            self.var_types[var_name] = vtype
                            decl = "String " if vtype == "string" else ("double " if vtype == "double" else "int ")
                            code += f"{indent}{decl}{line};\n"
                        else:
                            code += f"{indent}{line};\n"
                    else:
                        code += f"{indent}{line};\n"
            code += self._generate_java(self._get_next_node(node, 0), visited, indent_level)

        elif title == "Input":
            var_name = node.properties.get("variable", "user_in").strip()
            prompt = node.properties.get("prompt", "").strip()
            code += f"{indent}System.out.print(\"{prompt} \");\n"
            if var_name not in self.var_types:
                self.var_types[var_name] = "double"
                code += f"{indent}double {var_name} = scanner.nextDouble();\n"
            else:
                code += f"{indent}{var_name} = scanner.nextDouble();\n"
            code += self._generate_java(self._get_next_node(node, 0), visited, indent_level)

        elif title == "Output":
            expr = node.properties.get("expression", "''").strip()
            code += f"{indent}System.out.println({expr});\n"
            code += self._generate_java(self._get_next_node(node, 0), visited, indent_level)

        elif title == "Decision":
            cond = node.properties.get("condition", "true").strip()
            cond = self._translate_cond(cond, "java")
            code += f"{indent}if ({cond}) {{\n"
            
            true_node = self._get_next_node(node, 0)
            if true_node:
                code += self._generate_java(true_node, set(visited), indent_level + 1)

            false_node = self._get_next_node(node, 1)
            if false_node:
                code += f"{indent}}} else {{\n"
                code += self._generate_java(false_node, set(visited), indent_level + 1)
                
            code += f"{indent}}}\n"

        elif title == "While":
            cond = node.properties.get("condition", "true").strip()
            cond = self._translate_cond(cond, "java")
            code += f"{indent}while ({cond}) {{\n"
            
            loop_node = self._get_next_node(node, 0)
            if loop_node:
                code += self._generate_java(loop_node, set(visited), indent_level + 1)
                
            code += f"{indent}}}\n"
            exit_node = self._get_next_node(node, 1)
            if exit_node:
                code += self._generate_java(exit_node, visited, indent_level)

        elif title == "For":
            var_name = node.properties.get("variable", "i")
            start = node.properties.get("start", "0")
            end = node.properties.get("end", "10")
            step = node.properties.get("step", "1")
            
            code += f"{indent}for (int {var_name} = {start}; {var_name} < {end}; {var_name} += {step}) {{\n"
            loop_node = self._get_next_node(node, 0)
            if loop_node:
                code += self._generate_java(loop_node, set(visited), indent_level + 1)
                
            code += f"{indent}}}\n"
            exit_node = self._get_next_node(node, 1)
            if exit_node:
                code += self._generate_java(exit_node, visited, indent_level)

        elif title == "Function":
            func_name = getattr(node, "function_name", node.properties.get("function_name", "my_func"))
            params = node.properties.get("parameters", "")
            j_params = [f"double {p.strip()}" for p in params.split(",") if p.strip()]
            param_str = ", ".join(j_params)
            
            code += f"\n{indent}public static double {func_name}({param_str}) {{\n"
            inner = self._generate_java(self._get_next_node(node, 0), visited, indent_level + 1)
            code += inner
            code += f"{indent}}}\n"
                
        elif title == "Return":
            expr = node.properties.get("expression", "0")
            code += f"{indent}return {expr};\n"
            
        return code
