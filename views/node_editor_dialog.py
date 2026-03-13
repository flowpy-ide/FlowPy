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
