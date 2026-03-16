# views/node_editor_dialog.py
# ──────────────────────────────────────────────────────────────────────
# NodeEditorDialog : Düğüm tipine göre dinamik düzenleme formu
# ──────────────────────────────────────────────────────────────────────

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QPlainTextEdit, QDialogButtonBox,
                              QFormLayout, QGroupBox, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class NodeEditorDialog(QDialog):
    """Düğüm özelliklerini düzenlemek için açılan diyalog penceresi."""

    def __init__(self, node, parent=None):
        super().__init__(parent)
        self.node = node
        self.node_type = node.title
        self._inputs = {}  # alan adı → widget eşlemesi

        self.setWindowTitle(f"Düğüm Düzenle — {self.node_type}")
        self.setMinimumWidth(420)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # ── Başlık ────────────────────────────────────────────────────
        title_label = QLabel(f"📦  {self.node_type} Düğümü")
        title_font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # ── Tip bazlı form alanları ──────────────────────────────────
        form_group = QGroupBox("Özellikler")
        form_layout = QFormLayout(form_group)

        if self.node_type == "Decision":
            self._add_decision_fields(form_layout)
        elif self.node_type == "While":
            self._add_while_fields(form_layout)
        elif self.node_type == "Process":
            self._add_process_fields(form_layout)
        elif self.node_type == "Start":
            self._add_start_fields(form_layout)
        elif self.node_type == "Input":
            self._add_input_fields(form_layout)
        elif self.node_type == "Output":
            self._add_output_fields(form_layout)
        elif self.node_type == "For":
            self._add_for_fields(form_layout)
        elif self.node_type == "Function":
            self._add_function_fields(form_layout)
        elif self.node_type == "Return":
            self._add_return_fields(form_layout)
        else:
            self._add_generic_fields(form_layout)

        layout.addWidget(form_group)

        # ── OK / İptal butonları ─────────────────────────────────────
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ── Decision Alanları ────────────────────────────────────────────

    def _add_decision_fields(self, form: QFormLayout):
        # Koşul ifadesi
        cond_edit = QLineEdit()
        cond_edit.setPlaceholderText("Örnek: x > 5")
        cond_edit.setText(self.node.properties.get("condition", ""))
        form.addRow("Koşul İfadesi:", cond_edit)
        self._inputs["condition"] = cond_edit

        # Açıklama
        desc_edit = QLineEdit()
        desc_edit.setPlaceholderText("Bu karar ne hakkında?")
        desc_edit.setText(self.node.properties.get("description", ""))
        form.addRow("Açıklama:", desc_edit)
        self._inputs["description"] = desc_edit

    # ── While Alanları ───────────────────────────────────────────────

    def _add_while_fields(self, form: QFormLayout):
        # Döngü koşulu
        cond_edit = QLineEdit()
        cond_edit.setPlaceholderText("Örnek: i < 10")
        cond_edit.setText(self.node.properties.get("condition", ""))
        form.addRow("Döngü Koşulu:", cond_edit)
        self._inputs["condition"] = cond_edit

        # Açıklama
        desc_edit = QLineEdit()
        desc_edit.setPlaceholderText("Bu döngü ne yapıyor?")
        desc_edit.setText(self.node.properties.get("description", ""))
        form.addRow("Açıklama:", desc_edit)
        self._inputs["description"] = desc_edit

    # ── Process Alanları ─────────────────────────────────────────────

    def _add_process_fields(self, form: QFormLayout):
        # Python kodu
        code_edit = QPlainTextEdit()
        code_edit.setPlaceholderText("Örnek:\nresult = x + 10\nprint(result)")
        code_edit.setPlainText(self.node.properties.get("code", ""))
        code_edit.setMinimumHeight(120)
        code_font = QFont("Consolas", 10)
        code_edit.setFont(code_font)
        form.addRow("Python Kodu:", code_edit)
        self._inputs["code"] = code_edit

        # Açıklama
        desc_edit = QLineEdit()
        desc_edit.setPlaceholderText("Bu işlem ne yapıyor?")
        desc_edit.setText(self.node.properties.get("description", ""))
        form.addRow("Açıklama:", desc_edit)
        self._inputs["description"] = desc_edit

    # ── Start Alanları ───────────────────────────────────────────────

    def _add_start_fields(self, form: QFormLayout):
        # Başlangıç değişkenleri
        vars_edit = QPlainTextEdit()
        vars_edit.setPlaceholderText("Örnek:\nx = 10\ny = 20\nname = 'FlowPy'")
        vars_edit.setPlainText(self.node.properties.get("variables", ""))
        vars_edit.setMinimumHeight(100)
        vars_font = QFont("Consolas", 10)
        vars_edit.setFont(vars_font)
        form.addRow("Başlangıç Değişkenleri:", vars_edit)
        self._inputs["variables"] = vars_edit

    # ── Input Alanları ───────────────────────────────────────────────
    def _add_input_fields(self, form: QFormLayout):
        var_edit = QLineEdit()
        var_edit.setPlaceholderText("Değişken Adı (ör: name)")
        var_edit.setText(self.node.properties.get("variable", "USER_IN"))
        form.addRow("Değişken:", var_edit)
        self._inputs["variable"] = var_edit

        prompt_edit = QLineEdit()
        prompt_edit.setPlaceholderText("Kullanıcıya sorulacak soru")
        prompt_edit.setText(self.node.properties.get("prompt", "Değer girin:"))
        form.addRow("Soru (Prompt):", prompt_edit)
        self._inputs["prompt"] = prompt_edit

    # ── Output Alanları ──────────────────────────────────────────────
    def _add_output_fields(self, form: QFormLayout):
        expr_edit = QLineEdit()
        expr_edit.setPlaceholderText("Örnek: 'Merhaba ' + name")
        expr_edit.setText(self.node.properties.get("expression", ""))
        form.addRow("Çıktı İfadesi:", expr_edit)
        self._inputs["expression"] = expr_edit

    # ── For Loop Alanları ────────────────────────────────────────────
    def _add_for_fields(self, form: QFormLayout):
        var_edit = QLineEdit()
        var_edit.setText(self.node.properties.get("variable", "i"))
        form.addRow("Sayaç Değişkeni:", var_edit)
        self._inputs["variable"] = var_edit

        start_edit = QLineEdit()
        start_edit.setText(self.node.properties.get("start", "0"))
        form.addRow("Başlangıç:", start_edit)
        self._inputs["start"] = start_edit

        end_edit = QLineEdit()
        end_edit.setText(self.node.properties.get("end", "10"))
        form.addRow("Bitiş (Dahil Değil):", end_edit)
        self._inputs["end"] = end_edit

        step_edit = QLineEdit()
        step_edit.setText(self.node.properties.get("step", "1"))
        form.addRow("Artış (Step):", step_edit)
        self._inputs["step"] = step_edit

    # ── Function Alanları ────────────────────────────────────────────
    def _add_function_fields(self, form: QFormLayout):
        func_edit = QLineEdit()
        func_edit.setText(self.node.properties.get("function_name", "my_func"))
        form.addRow("Fonksiyon Adı:", func_edit)
        self._inputs["function_name"] = func_edit

        params_edit = QLineEdit()
        params_edit.setPlaceholderText("virgülle ayırın, ör: x, y")
        params_edit.setText(self.node.properties.get("parameters", ""))
        form.addRow("Parametreler:", params_edit)
        self._inputs["parameters"] = params_edit

    # ── Return Alanları ──────────────────────────────────────────────
    def _add_return_fields(self, form: QFormLayout):
        expr_edit = QLineEdit()
        expr_edit.setPlaceholderText("Geri döndürülecek ifade (ör: x + 10)")
        expr_edit.setText(self.node.properties.get("expression", ""))
        form.addRow("Dönüş İfadesi:", expr_edit)
        self._inputs["expression"] = expr_edit

    # ── Genel Alanlar ────────────────────────────────────────────────
    def _add_generic_fields(self, form: QFormLayout):
        desc_edit = QLineEdit()
        desc_edit.setText(self.node.properties.get("description", ""))
        form.addRow("Açıklama:", desc_edit)
        self._inputs["description"] = desc_edit

    # ── Sonuç ────────────────────────────────────────────────────────

    def get_properties(self) -> dict:
        """Kullanıcının girdiği değerleri dictionary olarak döndürür."""
        result = {}
        for key, widget in self._inputs.items():
            if isinstance(widget, QPlainTextEdit):
                result[key] = widget.toPlainText()
            elif isinstance(widget, QLineEdit):
                result[key] = widget.text()
            elif isinstance(widget, QComboBox):
                result[key] = widget.currentText()
        return result
