# views/node_editor_dialog.py
# ──────────────────────────────────────────────────────────────────────
# NodeEditorDialog : Düğüm tipine göre dinamik düzenleme formu (TR/EN)
# ──────────────────────────────────────────────────────────────────────

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
    QDialogButtonBox, QFormLayout, QGroupBox, QComboBox,
)
from PyQt6.QtGui import QFont

from core.i18n_nodes import (
    NODE_PROPERTY_SCHEMA, tn, t_node, t_prop, resolve_canonical_node_title,
)


class NodeEditorDialog(QDialog):
    """Düğüm özelliklerini düzenlemek için açılan diyalog penceresi."""

    def __init__(self, node, parent=None):
        super().__init__(parent)
        self.node = node
        self.node_type = resolve_canonical_node_title(node.title)
        if self.node_type != node.title:
            node.title = self.node_type
        self._inputs = {}

        display = t_node(self.node_type)
        self.setWindowTitle(tn("dialog_edit_node", name=display))
        self.setMinimumWidth(420)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        display = t_node(self.node_type)

        title_label = QLabel(tn("dialog_node_title", name=display))
        title_font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        form_group = QGroupBox(tn("dialog_properties"))
        form_layout = QFormLayout(form_group)

        if self.node_type in NODE_PROPERTY_SCHEMA:
            self._add_schema_fields(form_layout, NODE_PROPERTY_SCHEMA[self.node_type])
        else:
            self._add_generic_fields(form_layout)

        layout.addWidget(form_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _add_schema_fields(self, form: QFormLayout, schema: list):
        for prop_key, label_key, default in schema:
            current = self.node.properties.get(prop_key, default)
            if prop_key == "input_type":
                widget = QComboBox()
                widget.addItems(["auto", "int", "float", "str"])
                widget.setCurrentText(str(current) or "auto")
            elif prop_key in ("text", "code", "variables") or "\n" in str(current):
                widget = QPlainTextEdit()
                widget.setPlainText(str(current))
                widget.setMinimumHeight(80 if prop_key != "variables" else 100)
                widget.setFont(QFont("Consolas", 10))
            else:
                widget = QLineEdit()
                widget.setText(str(current))
            form.addRow(f"{t_prop(label_key)}:", widget)
            self._inputs[prop_key] = widget

    def _add_decision_fields(self, form: QFormLayout):
        cond_edit = QLineEdit()
        cond_edit.setText(self.node.properties.get("condition", ""))
        form.addRow(f"{t_prop('prop_condition')}:", cond_edit)
        self._inputs["condition"] = cond_edit

        desc_edit = QLineEdit()
        desc_edit.setText(self.node.properties.get("description", ""))
        form.addRow(f"{t_prop('prop_description')}:", desc_edit)
        self._inputs["description"] = desc_edit

    def _add_while_fields(self, form: QFormLayout):
        cond_edit = QLineEdit()
        cond_edit.setText(self.node.properties.get("condition", ""))
        form.addRow(f"{t_prop('prop_loop_condition')}:", cond_edit)
        self._inputs["condition"] = cond_edit

        desc_edit = QLineEdit()
        desc_edit.setText(self.node.properties.get("description", ""))
        form.addRow(f"{t_prop('prop_description')}:", desc_edit)
        self._inputs["description"] = desc_edit

    def _add_process_fields(self, form: QFormLayout):
        code_edit = QPlainTextEdit()
        code_edit.setPlainText(self.node.properties.get("code", ""))
        code_edit.setMinimumHeight(120)
        code_edit.setFont(QFont("Consolas", 10))
        form.addRow(f"{t_prop('prop_code')}:", code_edit)
        self._inputs["code"] = code_edit

        desc_edit = QLineEdit()
        desc_edit.setText(self.node.properties.get("description", ""))
        form.addRow(f"{t_prop('prop_description')}:", desc_edit)
        self._inputs["description"] = desc_edit

    def _add_start_fields(self, form: QFormLayout):
        vars_edit = QPlainTextEdit()
        vars_edit.setPlainText(self.node.properties.get("variables", ""))
        vars_edit.setMinimumHeight(100)
        vars_edit.setFont(QFont("Consolas", 10))
        form.addRow(f"{t_prop('prop_variables')}:", vars_edit)
        self._inputs["variables"] = vars_edit

    def _add_input_fields(self, form: QFormLayout):
        var_edit = QLineEdit()
        var_edit.setText(self.node.properties.get("variable", "USER_IN"))
        form.addRow(f"{t_prop('prop_variable')}:", var_edit)
        self._inputs["variable"] = var_edit

        prompt_edit = QLineEdit()
        prompt_edit.setText(self.node.properties.get("prompt", "Değer girin:"))
        form.addRow(f"{t_prop('prop_prompt')}:", prompt_edit)
        self._inputs["prompt"] = prompt_edit

        type_combo = QComboBox()
        type_combo.addItems(["auto", "int", "float", "str"])
        type_combo.setCurrentText(self.node.properties.get("input_type", "auto"))
        form.addRow(f"{t_prop('prop_input_type')}:", type_combo)
        self._inputs["input_type"] = type_combo

    def _add_output_fields(self, form: QFormLayout):
        expr_edit = QLineEdit()
        expr_edit.setText(self.node.properties.get("expression", ""))
        form.addRow(f"{t_prop('prop_output_expression')}:", expr_edit)
        self._inputs["expression"] = expr_edit

    def _add_for_fields(self, form: QFormLayout):
        defaults = {"variable": "i", "start": "0", "end": "10", "step": "1"}
        labels = {
            "variable": "prop_counter",
            "start": "prop_start",
            "end": "prop_end",
            "step": "prop_step",
        }
        for key, label_key in labels.items():
            edit = QLineEdit()
            edit.setText(self.node.properties.get(key, defaults[key]))
            form.addRow(f"{t_prop(label_key)}:", edit)
            self._inputs[key] = edit

    def _add_function_fields(self, form: QFormLayout):
        func_edit = QLineEdit()
        func_edit.setText(self.node.properties.get("function_name", "my_func"))
        form.addRow(f"{t_prop('prop_function_name')}:", func_edit)
        self._inputs["function_name"] = func_edit

        params_edit = QLineEdit()
        params_edit.setText(self.node.properties.get("parameters", ""))
        form.addRow(f"{t_prop('prop_parameters')}:", params_edit)
        self._inputs["parameters"] = params_edit

    def _add_return_fields(self, form: QFormLayout):
        expr_edit = QLineEdit()
        expr_edit.setText(self.node.properties.get("expression", ""))
        form.addRow(f"{t_prop('prop_return_expression')}:", expr_edit)
        self._inputs["expression"] = expr_edit

    def _add_generic_fields(self, form: QFormLayout):
        desc_edit = QLineEdit()
        desc_edit.setText(self.node.properties.get("description", ""))
        form.addRow(f"{t_prop('prop_description')}:", desc_edit)
        self._inputs["description"] = desc_edit

    def get_properties(self) -> dict:
        result = {}
        for key, widget in self._inputs.items():
            if isinstance(widget, QPlainTextEdit):
                result[key] = widget.toPlainText()
            elif isinstance(widget, QLineEdit):
                result[key] = widget.text()
            elif isinstance(widget, QComboBox):
                result[key] = widget.currentText()
        return result
