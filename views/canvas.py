# views/canvas.py
# ──────────────────────────────────────────────────────────────────────
# FlowScene : QGraphicsScene alt sınıfı — sürükle-bırak ile
#              düğüm oluşturma, port bağlantıları ve NodeRegistry.
# ──────────────────────────────────────────────────────────────────────

from PyQt6.QtWidgets import QGraphicsScene, QGraphicsPathItem
from PyQt6.QtCore import Qt, QByteArray, QDataStream, QIODevice, QPointF
from PyQt6.QtGui import QPen, QColor, QPainterPath

from models.node import BaseNode, Port
from models.edge import Edge
from core.registry import NodeRegistry

# QListWidget'in kullandığı varsayılan sürükleme formatı
_LIST_MIME = "application/x-qabstractitemmodeldatalist"


class FlowScene(QGraphicsScene):
    """Sürükle-bırak destekli düğüm sahne yöneticisi."""

    def __init__(self, registry: NodeRegistry, parent=None):
        super().__init__(parent)
        self.registry = registry
        # Varsayılan sahne boyutu
        self.setSceneRect(-1000, -1000, 2000, 2000)

        # ── Bağlantı durumu ──────────────────────────────────────────
        self._connecting = False       # Bağlantı çizimi aktif mi?
        self._source_port = None       # Başlangıç portu
        self._temp_edge = None         # Geçici Bezier çizgisi

    # ══════════════════════════════════════════════════════════════════
    #  Bağlantı (Edge) Oluşturma — Port tıklama ile
    # ══════════════════════════════════════════════════════════════════

    def start_connection(self, port: Port):
        """Bir porta tıklandığında çağrılır — geçici çizgi başlatır."""
        self._connecting = True
        self._source_port = port

        # Geçici Bezier çizgisi oluştur
        self._temp_edge = QGraphicsPathItem()
        self._temp_edge.setPen(QPen(QColor("#e74c3c"), 2, Qt.PenStyle.DashLine))
        self._temp_edge.setZValue(-1)
        self.addItem(self._temp_edge)

    def update_connection(self, scene_pos: QPointF):
        """Fare sürüklenirken geçici Bezier çizgisini günceller."""
        if not self._connecting or not self._temp_edge:
            return

        r = Port.RADIUS
        src = self._source_port.scenePos() + QPointF(r, r)
        dst = scene_pos

        # Bezier kontrol noktaları
        offset = abs(dst.x() - src.x()) * 0.5
        if offset < 50:
            offset = 50

        ctrl1 = src + QPointF(offset, 0)
        ctrl2 = dst - QPointF(offset, 0)

        path = QPainterPath(src)
        path.cubicTo(ctrl1, ctrl2, dst)
        self._temp_edge.setPath(path)

    def finish_connection(self, scene_pos: QPointF):
        """Fare bırakıldığında: hedef port varsa Edge oluştur, yoksa iptal."""
        if not self._connecting:
            return

        # Geçici çizgiyi temizle
        if self._temp_edge:
            self.removeItem(self._temp_edge)
            self._temp_edge = None

        # Bırakılan noktadaki öğeleri kontrol et
        target_port = None
        items = self.items(scene_pos)
        for item in items:
            if isinstance(item, Port) and item is not self._source_port:
                target_port = item
                break

        # Geçerli bağlantı kurallarını kontrol et
        if target_port and self._is_valid_connection(self._source_port, target_port):
            # Kaynak ve hedef düğümleri belirle
            src_node = self._source_port.parentItem()
            dst_node = target_port.parentItem()

            # Çıkış → Giriş yönünü garanti et
            if self._source_port.is_output:
                edge = Edge(src_node, dst_node,
                            source_port=self._source_port,
                            dest_port=target_port)
            else:
                edge = Edge(dst_node, src_node,
                            source_port=target_port,
                            dest_port=self._source_port)

            self.addItem(edge)

            # Registry'ye kenarı kaydet
            self.registry.add_edge(
                edge.source_node.node_id,
                edge.dest_node.node_id
            )

        # Durumu sıfırla
        self._connecting = False
        self._source_port = None

    @staticmethod
    def _is_valid_connection(port_a: Port, port_b: Port) -> bool:
        """İki port arasında bağlantı kurulabilir mi?
        Kurallar:
          - Farklı türde olmalılar (biri input, biri output)
          - Aynı düğümün portları olmamalılar
        """
        if port_a.is_output == port_b.is_output:
            return False  # İkisi de input veya ikisi de output
        if port_a.parentItem() is port_b.parentItem():
            return False  # Aynı düğüm
        return True

    # ══════════════════════════════════════════════════════════════════
    #  Sürükle-Bırak (Panelden Düğüm Ekleme)
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def _accepts(mime_data) -> bool:
        """Sürükleme verisinin kabul edilebilir formatta olup olmadığını döndürür."""
        return mime_data.hasText() or mime_data.hasFormat(_LIST_MIME)

    @staticmethod
    def _extract_text(mime_data) -> str:
        """Mime verisinden düğüm adını çıkarır."""
        if mime_data.hasText():
            return mime_data.text().strip()

        if mime_data.hasFormat(_LIST_MIME):
            data = mime_data.data(_LIST_MIME)
            stream = QDataStream(data, QIODevice.OpenModeFlag.ReadOnly)
            while not stream.atEnd():
                row = stream.readInt32()
                col = stream.readInt32()
                map_items = stream.readInt32()
                for _ in range(map_items):
                    role = stream.readInt32()
                    value = stream.readQVariant()
                    if role == Qt.ItemDataRole.DisplayRole:
                        text = str(value).strip()
                        if text:
                            return text
        return ""

    def dragEnterEvent(self, event):
        if self._accepts(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if self._accepts(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        node_type = self._extract_text(event.mimeData())
        if not node_type:
            event.ignore()
            return

        scene_pos = event.scenePos()
        node = BaseNode(title=node_type)
        node_id = self.registry.add_node(node)
        node.node_id = node_id
        self.addItem(node)
        node.setPos(scene_pos)
        event.acceptProposedAction()

    # ══════════════════════════════════════════════════════════════════
    #  Silme & Bağlam Menüsü
    # ══════════════════════════════════════════════════════════════════

    def keyPressEvent(self, event):
        """Delete tuşu ile seçili öğeleri sil."""
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.delete_selected()
        else:
            super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        """Sağ tık bağlam menüsü."""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction

        menu = QMenu()

        # Tıklanan noktadaki öğeyi kontrol et
        item = self.itemAt(event.scenePos(), self.views()[0].transform())
        target_node = None
        if isinstance(item, BaseNode):
            target_node = item
        elif isinstance(item, Port):
            target_node = item.parentItem()

        if target_node and isinstance(target_node, BaseNode):
            edit_action = QAction(f"✏️  Düzenle: {target_node.title}", menu)
            edit_action.triggered.connect(
                lambda: target_node.mouseDoubleClickEvent(None)
            )
            menu.addAction(edit_action)
            menu.addSeparator()

        # Seçili öğe varsa sil seçeneği
        if self.selectedItems():
            count = len([i for i in self.selectedItems()
                         if isinstance(i, (BaseNode, Edge))])
            if count:
                del_action = QAction(f"🗑️  Seçilenleri Sil ({count})", menu)
                del_action.triggered.connect(self.delete_selected)
                menu.addAction(del_action)

        select_all_action = QAction("☐  Tümünü Seç", menu)
        select_all_action.triggered.connect(self._select_all)
        menu.addAction(select_all_action)

        menu.exec(event.screenPos())

    def delete_selected(self):
        """Seçili düğüm ve edge'leri sahneden ve registry'den siler."""
        items = self.selectedItems()
        if not items:
            return

        # Önce edge'leri sil (sonra node silince referans sorununu önle)
        for item in list(items):
            if isinstance(item, Edge):
                self._remove_edge(item)

        # Sonra node'ları sil
        for item in list(items):
            if isinstance(item, BaseNode):
                self._remove_node(item)

    def _remove_node(self, node: BaseNode):
        """Düğümü ve ona bağlı tüm edge'leri siler."""
        # Bağlı edge'leri temizle
        for edge in list(node.edges):
            self._remove_edge(edge)

        # Registry'den sil
        self.registry.remove_node(node.node_id)

        # Sahneden kaldır
        self.removeItem(node)

    def _remove_edge(self, edge: Edge):
        """Edge'i sahneden, düğümlerin listelerinden ve registry'den siler."""
        # Düğümlerin edge listelerinden çıkar
        if edge.source_node and edge in edge.source_node.edges:
            edge.source_node.edges.remove(edge)
        if edge.dest_node and edge in edge.dest_node.edges:
            edge.dest_node.edges.remove(edge)

        # Registry'den edge'i kaldır
        self.registry.edges = [
            (s, d) for s, d in self.registry.edges
            if not (s == edge.source_node.node_id and d == edge.dest_node.node_id)
        ]

        # Sahneden kaldır
        if edge.scene():
            self.removeItem(edge)

    def _select_all(self):
        """Tüm düğümleri seçer."""
        for item in self.items():
            if isinstance(item, BaseNode):
                item.setSelected(True)
