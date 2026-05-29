# views/canvas.py
# ──────────────────────────────────────────────────────────────────────
# FlowScene : QGraphicsScene alt sınıfı — sürükle-bırak ile
#              düğüm oluşturma, port bağlantıları ve NodeRegistry.
# HorizontalRuler / VerticalRuler: canvas kenar cetvelleri.
# ──────────────────────────────────────────────────────────────────────

from PyQt6.QtWidgets import QGraphicsScene, QGraphicsPathItem, QWidget
from PyQt6.QtCore import Qt, QByteArray, QDataStream, QIODevice, QPointF, QObject, QEvent, pyqtSignal, QRectF
from PyQt6.QtGui import QPen, QColor, QPainterPath, QBrush, QPainter, QFont

from models.node import BaseNode, Port
from models.edge import Edge
from core.registry import NodeRegistry
from core.i18n_nodes import resolve_canonical_node_title

# QListWidget / QTreeWidget'in kullandığı varsayılan sürükleme formatı
_LIST_MIME = "application/x-qabstractitemmodeldatalist"


# ═══════════════════════════════════════════════════════════════════════
#  Cetvel Widgetları
# ═══════════════════════════════════════════════════════════════════════

class HorizontalRuler(QWidget):
    """Canvas'ın üst kenarında piksel cetveli çizer (yatay)."""

    HEIGHT = 22
    TICK_INTERVAL = 100   # her kaç px'de bir büyük işaret

    def __init__(self, view, parent=None):
        super().__init__(parent or view.parent())
        self.view = view
        self.setFixedHeight(self.HEIGHT)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#252525"))

        pen = QPen(QColor("#555"), 1)
        painter.setPen(pen)
        # Cetvel alt çizgisi
        painter.drawLine(0, self.HEIGHT - 1, self.width(), self.HEIGHT - 1)

        font = QFont("Segoe UI", 7)
        painter.setFont(font)
        painter.setPen(QColor("#888"))

        # Görünür sahne aralığını hesapla
        view = self.view
        left_scene = view.mapToScene(0, 0).x()
        right_scene = view.mapToScene(self.width(), 0).x()

        step = self.TICK_INTERVAL
        start = int(left_scene // step) * step

        for scene_x in range(start, int(right_scene) + step, step):
            vp_x = int(view.mapFromScene(QPointF(scene_x, 0)).x())
            if 0 <= vp_x <= self.width():
                painter.setPen(QPen(QColor("#666"), 1))
                painter.drawLine(vp_x, self.HEIGHT - 8, vp_x, self.HEIGHT - 1)
                painter.setPen(QColor("#888"))
                painter.drawText(vp_x + 2, self.HEIGHT - 8, str(scene_x))

        painter.end()


class VerticalRuler(QWidget):
    """Canvas'ın sol kenarında piksel cetveli çizer (dikey)."""

    WIDTH = 22
    TICK_INTERVAL = 100

    def __init__(self, view, parent=None):
        super().__init__(parent or view.parent())
        self.view = view
        self.setFixedWidth(self.WIDTH)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#252525"))

        painter.setPen(QPen(QColor("#555"), 1))
        # Cetvel sağ çizgisi
        painter.drawLine(self.WIDTH - 1, 0, self.WIDTH - 1, self.height())

        font = QFont("Segoe UI", 7)
        painter.setFont(font)
        painter.setPen(QColor("#888"))

        view = self.view
        top_scene = view.mapToScene(0, 0).y()
        bot_scene = view.mapToScene(0, self.height()).y()

        step = self.TICK_INTERVAL
        start = int(top_scene // step) * step

        for scene_y in range(start, int(bot_scene) + step, step):
            vp_y = int(view.mapFromScene(QPointF(0, scene_y)).y())
            if 0 <= vp_y <= self.height():
                painter.setPen(QPen(QColor("#666"), 1))
                painter.drawLine(self.WIDTH - 8, vp_y, self.WIDTH - 1, vp_y)
                painter.setPen(QColor("#888"))
                painter.save()
                painter.translate(self.WIDTH - 10, vp_y - 2)
                painter.rotate(-90)
                painter.drawText(0, 0, str(scene_y))
                painter.restore()

        painter.end()


class ZoomPanFilter(QObject):
    """QGraphicsView üzerinde zoom (Ctrl+Wheel) ve pan (Orta Tuş) işlemlerini yönetir."""
    
    def __init__(self, view, parent=None):
        super().__init__(parent)
        self.view = view
        self._pan_active = False
        self._pan_start_x = 0
        self._pan_start_y = 0

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel:
            # Ctrl + Wheel ile Zoom
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                # Zoom in / out hesapla
                zoom_in_factor = 1.15
                zoom_out_factor = 1.0 / zoom_in_factor
                
                # Tekerleğin yönüne göre zoom faktörü seç
                if event.angleDelta().y() > 0:
                    zoom_factor = zoom_in_factor
                else:
                    zoom_factor = zoom_out_factor
                    
                self.view.scale(zoom_factor, zoom_factor)
                return True
                
        elif event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.MiddleButton:
                self._pan_active = True
                self._pan_start_x = event.globalPosition().x()
                self._pan_start_y = event.globalPosition().y()
                self.view.setCursor(Qt.CursorShape.ClosedHandCursor)
                return True
                
        elif event.type() == QEvent.Type.MouseMove:
            if self._pan_active:
                dx = event.globalPosition().x() - self._pan_start_x
                dy = event.globalPosition().y() - self._pan_start_y
                self._pan_start_x = event.globalPosition().x()
                self._pan_start_y = event.globalPosition().y()
                
                # Scroll barların değerini değiştirerek pan yap
                scroll_x = self.view.horizontalScrollBar()
                scroll_y = self.view.verticalScrollBar()
                scroll_x.setValue(int(scroll_x.value() - dx))
                scroll_y.setValue(int(scroll_y.value() - dy))
                return True
                
        elif event.type() == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.MiddleButton:
                self._pan_active = False
                self.view.setCursor(Qt.CursorShape.ArrowCursor)
                return True

        return super().eventFilter(obj, event)


class FlowScene(QGraphicsScene):
    """Sürükle-bırak destekli düğüm sahne yöneticisi."""
    
    history_changed = pyqtSignal()

    def __init__(self, registry: NodeRegistry, parent=None):
        super().__init__(parent)
        self.registry = registry
        self.setSceneRect(-3000, -500, 6000, 4000)

        # ── Koyu Grid Arkaplan ───────────────────────────────────────
        self.setBackgroundBrush(QBrush(QColor("#1e1e1e")))
        self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.BspTreeIndex)

        # ── Bağlantı durumu ──────────────────────────────────────────
        self._connecting = False       # Bağlantı çizimi aktif mi?
        self._source_port = None       # Başlangıç portu
        self._temp_edge = None         # Geçici Bezier çizgisi
        self._clipboard: list[dict] = []

    def fit_scene_rect_to_contents(self, margin: float = 500.0):
        """Tüm öğelere göre sahne dikdörtgenini günceller (kaydırma alanı)."""
        rect = self.itemsBoundingRect()
        if rect.isNull() or rect.isEmpty():
            return
        padded = rect.adjusted(-margin, -margin, margin, margin)
        self.setSceneRect(padded)

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
            self.history_changed.emit()

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

    def drawBackground(self, painter: QPainter, rect):
        """Koyu tema ızgara desenli arkaplan çizer."""
        super().drawBackground(painter, rect)
        
        left = int(rect.left()) - (int(rect.left()) % 20)
        top = int(rect.top()) - (int(rect.top()) % 20)
        
        lines = []
        # Küçük grid çizgileri (her 20px)
        for x in range(left, int(rect.right()), 20):
            lines.append(QPointF(x, rect.top()))
            lines.append(QPointF(x, rect.bottom()))
        for y in range(top, int(rect.bottom()), 20):
            lines.append(QPointF(rect.left(), y))
            lines.append(QPointF(rect.right(), y))
            
        painter.setPen(QPen(QColor("#2c2c2c"), 1, Qt.PenStyle.SolidLine))
        painter.drawLines(lines)
        
        # Büyük grid çizgileri (her 100px)
        left = int(rect.left()) - (int(rect.left()) % 100)
        top = int(rect.top()) - (int(rect.top()) % 100)
        
        thick_lines = []
        for x in range(left, int(rect.right()), 100):
            thick_lines.append(QPointF(x, rect.top()))
            thick_lines.append(QPointF(x, rect.bottom()))
        for y in range(top, int(rect.bottom()), 100):
            thick_lines.append(QPointF(rect.left(), y))
            thick_lines.append(QPointF(rect.right(), y))
            
        painter.setPen(QPen(QColor("#3a3a3a"), 1, Qt.PenStyle.SolidLine))
        painter.drawLines(thick_lines)

    # ══════════════════════════════════════════════════════════════════
    #  Sürükle-Bırak (Panelden Düğüm Ekleme)
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def _accepts(mime_data) -> bool:
        """Sürükleme verisinin kabul edilebilir formatta olup olmadığını döndürür."""
        return mime_data.hasText() or mime_data.hasFormat(_LIST_MIME)

    @staticmethod
    def _extract_text(mime_data) -> str:
        """Mime verisinden kanonik düğüm adını çıkarır (UserRole öncelikli)."""
        if mime_data.hasFormat(_LIST_MIME):
            data = mime_data.data(_LIST_MIME)
            stream = QDataStream(data, QIODevice.OpenModeFlag.ReadOnly)
            user_role_text = ""
            display_text = ""
            while not stream.atEnd():
                row = stream.readInt32()   # noqa: F841
                col = stream.readInt32()   # noqa: F841
                map_items = stream.readInt32()
                for _ in range(map_items):
                    role = stream.readInt32()
                    value = stream.readQVariant()
                    if role == Qt.ItemDataRole.UserRole:
                        t = str(value).strip()
                        if t and t != "None":
                            user_role_text = t
                    elif role == Qt.ItemDataRole.DisplayRole:
                        t = str(value).strip()
                        if t:
                            display_text = t.lstrip()
            raw = user_role_text or display_text
            if raw:
                return resolve_canonical_node_title(raw)

        if mime_data.hasText():
            return resolve_canonical_node_title(mime_data.text().strip())
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
        self.history_changed.emit()

    # ══════════════════════════════════════════════════════════════════
    #  Silme & Bağlam Menüsü
    # ══════════════════════════════════════════════════════════════════

    def keyPressEvent(self, event):
        """Klavye kısayolları: sil, kopyala, yapıştır, çoğalt, seç."""
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.delete_selected()
            event.accept()
            return
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Z:
                event.ignore()
                return
            if event.key() == Qt.Key.Key_Y:
                event.ignore()
                return
            if event.key() == Qt.Key.Key_C:
                self.copy_selected()
                event.accept()
                return
            if event.key() == Qt.Key.Key_V:
                self.paste_nodes()
                event.accept()
                return
            if event.key() == Qt.Key.Key_A:
                self._select_all()
                event.accept()
                return
            if event.key() == Qt.Key.Key_D:
                self.copy_selected()
                self.paste_nodes()
                event.accept()
                return
        super().keyPressEvent(event)

    def copy_selected(self):
        """Seçili node'ları clipboard'a kopyalar."""
        self._clipboard.clear()
        selected_nodes = [i for i in self.selectedItems() if isinstance(i, BaseNode)]
        if not selected_nodes:
            return
        center_x = sum(n.pos().x() for n in selected_nodes) / len(selected_nodes)
        center_y = sum(n.pos().y() for n in selected_nodes) / len(selected_nodes)
        for node in selected_nodes:
            self._clipboard.append({
                "title": node.title,
                "properties": dict(node.properties),
                "rel_x": node.pos().x() - center_x,
                "rel_y": node.pos().y() - center_y,
                "_custom_color": getattr(node, "_custom_color", None),
            })

    def paste_nodes(self):
        """Clipboard'daki node'ları sahneye yapıştırır."""
        if not self._clipboard:
            return
        paste_x, paste_y = 40, 40
        self.clearSelection()
        for clip in self._clipboard:
            node = BaseNode(title=clip["title"])
            node.properties.update(clip["properties"])
            if clip.get("_custom_color"):
                node._custom_color = clip["_custom_color"]
            node_id = self.registry.add_node(node)
            node.node_id = node_id
            self.addItem(node)
            node.setPos(paste_x + clip["rel_x"], paste_y + clip["rel_y"])
            node.setSelected(True)
        self.history_changed.emit()

    def auto_layout(self, mode: str = "horizontal"):
        """Seçili veya tüm node'ları otomatik hizalar."""
        import math
        nodes = [i for i in self.selectedItems() if isinstance(i, BaseNode)]
        if not nodes:
            nodes = [i for i in self.items() if isinstance(i, BaseNode)]
        if not nodes:
            return
        spacing_x, spacing_y = 200, 120
        if mode == "horizontal":
            nodes.sort(key=lambda n: n.pos().x())
            start_x = nodes[0].pos().x()
            base_y = sum(n.pos().y() for n in nodes) / len(nodes)
            for i, node in enumerate(nodes):
                node.setPos(start_x + i * spacing_x, base_y)
        elif mode == "vertical":
            nodes.sort(key=lambda n: n.pos().y())
            base_x = sum(n.pos().x() for n in nodes) / len(nodes)
            start_y = nodes[0].pos().y()
            for i, node in enumerate(nodes):
                node.setPos(base_x, start_y + i * spacing_y)
        elif mode == "grid":
            cols = max(1, int(math.ceil(math.sqrt(len(nodes)))))
            for i, node in enumerate(nodes):
                node.setPos((i % cols) * spacing_x, (i // cols) * spacing_y)
        self.history_changed.emit()

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
            bp_text = (
                "🔴 Breakpoint Kaldır" if target_node._has_breakpoint
                else "🔴 Breakpoint Ekle"
            )
            bp_action = QAction(bp_text, menu)

            def toggle_bp(node=target_node):
                node.toggle_breakpoint()
                scene = node.scene()
                if scene and scene.views():
                    main = scene.views()[0].window()
                    if hasattr(main, "interpreter"):
                        main.interpreter.toggle_breakpoint(node.node_id)

            bp_action.triggered.connect(toggle_bp)
            menu.addAction(bp_action)

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
                
        self.history_changed.emit()

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
