"""Simple undo/redo command stack."""


class Command:
    """Base undoable command."""

    def do(self) -> None:
        pass

    def undo(self) -> None:
        pass


class AddItemCommand(Command):
    def __init__(self, scene, item) -> None:
        self.scene = scene
        self.item = item

    def do(self) -> None:
        if self.item.scene() is None:
            self.scene.addItem(self.item)

    def undo(self) -> None:
        self.scene.removeItem(self.item)


class RemoveItemCommand(Command):
    def __init__(self, scene, item) -> None:
        self.scene = scene
        self.item = item

    def do(self) -> None:
        self.scene.removeItem(self.item)

    def undo(self) -> None:
        if self.item.scene() is None:
            self.scene.addItem(self.item)


class CropCommand(Command):
    """Replace the base image by a cropped one; annotations are removed.

    Undo restores the previous base image and every removed item."""

    def __init__(self, scene, old_pixmap, cropped_pixmap, removed_items) -> None:
        self.scene = scene
        self.old_pixmap = old_pixmap
        self.cropped_pixmap = cropped_pixmap
        self.removed = list(removed_items)
        self._images = list(scene._image_items)

    def _show(self, pixmap) -> None:
        # The overlay window also resizes itself and refits the view.
        for view in self.scene.views():
            win = view.window()
            if hasattr(win, "set_image"):
                win.set_image(pixmap)
                return
        self.scene.set_base_image(pixmap)

    def do(self) -> None:
        self.scene.clearSelection()
        for item in self.removed:
            if item.scene() is self.scene:
                self.scene.removeItem(item)
        self.scene._image_items.clear()
        self._show(self.cropped_pixmap)

    def undo(self) -> None:
        self.scene.clearSelection()
        self._show(self.old_pixmap)
        for item in self.removed:
            if item.scene() is None:
                self.scene.addItem(item)
        self.scene._image_items[:] = self._images
        self.scene._expand_scene_if_needed()


class History:
    """Keeps undo/redo stacks."""

    def __init__(self) -> None:
        self._undo: list[Command] = []
        self._redo: list[Command] = []

    def push(self, cmd: Command) -> None:
        cmd.do()
        self._undo.append(cmd)
        self._redo.clear()

    def undo(self) -> None:
        if self._undo:
            cmd = self._undo.pop()
            cmd.undo()
            self._redo.append(cmd)

    def redo(self) -> None:
        if self._redo:
            cmd = self._redo.pop()
            cmd.do()
            self._undo.append(cmd)

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()

    def can_undo(self) -> bool:
        return bool(self._undo)

    def can_redo(self) -> bool:
        return bool(self._redo)
