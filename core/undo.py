# core/undo.py
# ──────────────────────────────────────────────────────────────────────
# UndoManager : Sahnenin durumunu JSON string'leri olarak saklar.
#               Kullanıcı geri veya ileri almak istediğinde JSON'dan
#               tekrar deserialize eder.
# ──────────────────────────────────────────────────────────────────────

import json
from PyQt6.QtCore import QObject
from core.serializer import FlowSerializer


class UndoManager(QObject):
    """Geri/İleri alma işlemlerini tam durum (snapshot) yedeği ile yönetir."""

    def __init__(self, registry, scene):
        super().__init__()
        self.registry = registry
        self.scene = scene
        
        self._undo_stack = []
        self._redo_stack = []
        self._is_undoing = False
        
        # İlk durumu kaydet
        self.save_snapshot()

    def save_snapshot(self):
        """Mevcut durumun JSON kopyasını alır ve yığına ekler."""
        if self._is_undoing:
            return  # Geri/ileri alma sırasında yeni kayıt tetiklenmesin
            
        data = FlowSerializer.serialize_to_dict(self.registry)
        state_str = json.dumps(data)

        # Ardışık aynı durumları kaydetmekten kaçın
        if self._undo_stack and self._undo_stack[-1] == state_str:
            return

        self._undo_stack.append(state_str)
        self._redo_stack.clear()  # Yeni bir hamle yapıldığında ileri yığını sıfırlanır
        
        # Stack çok büyümesin diye (örneğin 50 adım sınırı)
        if len(self._undo_stack) > 50:
            self._undo_stack.pop(0)

    def undo(self) -> bool:
        """Son durumu geri alır. Başarılıysa True döner."""
        if len(self._undo_stack) <= 1:
            return False

        self._is_undoing = True
        current_state = self._undo_stack.pop()
        self._redo_stack.append(current_state)
        previous_state = self._undo_stack[-1]
        data = json.loads(previous_state)
        FlowSerializer.deserialize_from_dict(data, self.registry, self.scene)
        self._is_undoing = False
        return True

    def redo(self) -> bool:
        """Geri alınan işlemi ileri sarar. Başarılıysa True döner."""
        if not self._redo_stack:
            return False

        self._is_undoing = True
        next_state = self._redo_stack.pop()
        self._undo_stack.append(next_state)
        data = json.loads(next_state)
        FlowSerializer.deserialize_from_dict(data, self.registry, self.scene)
        self._is_undoing = False
        return True
