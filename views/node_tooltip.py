# views/node_tooltip.py
# ──────────────────────────────────────────────────────────────────────
# NodeDocTooltip : Düğüm paleti hover dokümantasyon balonu.
# ──────────────────────────────────────────────────────────────────────

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPoint

from core.i18n_node_docs import get_node_doc


class NodeDocTooltip(QWidget):
    """Node'a hover edilince gösterilen detaylı tooltip."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Port tıklamalarını engellemesin — fare olayları alttaki canvas'a geçsin
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("""
            QWidget#tooltipRoot {
                background: #1e2030;
                border: 1px solid #3a4a6a;
                border-radius: 8px;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        root = QWidget(self)
        root.setObjectName("tooltipRoot")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(root)

        inner = QVBoxLayout(root)
        inner.setContentsMargins(12, 10, 12, 10)
        inner.setSpacing(6)

        self.title_label = QLabel()
        self.title_label.setStyleSheet(
            "color: #93c5fd; font-weight: bold; font-size: 12px; "
            "background: transparent; border: none;"
        )
        self.desc_label = QLabel()
        self.desc_label.setStyleSheet(
            "color: #aaa; font-size: 11px; background: transparent; border: none;"
        )
        self.desc_label.setWordWrap(True)
        self.example_label = QLabel()
        self.example_label.setStyleSheet("""
            color: #4ade80; font-size: 10px; font-family: Consolas, monospace;
            background: #0d1a0d; border: 1px solid #1a3a1a; border-radius: 4px;
            padding: 4px 6px;
        """)
        self.example_label.setWordWrap(True)
        self.tip_label = QLabel()
        self.tip_label.setStyleSheet(
            "color: #fbbf24; font-size: 10px; background: transparent; border: none;"
        )
        self.tip_label.setWordWrap(True)

        inner.addWidget(self.title_label)
        inner.addWidget(self.desc_label)
        inner.addWidget(self.example_label)
        inner.addWidget(self.tip_label)

        self.setMaximumWidth(280)
        self.setMinimumSize(1, 1)
        self._hide_timer = QTimer()
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

    def show_for_node(self, node_title: str, global_pos: QPoint, placement: str = "above"):
        doc = get_node_doc(node_title)
        if not doc:
            return
        self.title_label.setText(doc["title"])
        self.desc_label.setText(doc["desc"])
        self.example_label.setText(doc.get("example", ""))
        self.tip_label.setText(f"💡 {doc.get('tip', '')}")
        self.adjustSize()
        hint = self.sizeHint()
        self.resize(hint)

        if placement == "above":
            x = global_pos.x() - hint.width() // 2
            y = global_pos.y() - hint.height() - 10
        else:
            x = global_pos.x() + 15
            y = global_pos.y() + 10
        self.move(x, y)
        self.show()
        self._hide_timer.stop()

    def schedule_hide(self, delay_ms: int = 300):
        self._hide_timer.start(delay_ms)
