"""Simple undo/redo command stack."""


class Command:
    """Base undoable command."""

    def do(self) -> None:
        pass

    def undo(self) -> None:
        pass


def _sync_images(scene, item, present: bool) -> None:
    """Keep the scene's extra-image registry in step with undo/redo."""
    images = scene._image_items
    if present and item not in images:
        images.append(item)
    elif not present and item in images:
        images.remove(item)


class AddItemCommand(Command):
    def __init__(self, scene, item) -> None:
        self.scene = scene
        self.item = item
        self._is_image = item in scene._image_items

    def do(self) -> None:
        if self.item.scene() is None:
            self.scene.addItem(self.item)
        if self._is_image:
            _sync_images(self.scene, self.item, True)
        self.scene._expand_scene_if_needed()

    def undo(self) -> None:
        self.scene.removeItem(self.item)
        if self._is_image:
            _sync_images(self.scene, self.item, False)
        self.scene._expand_scene_if_needed()


class RemoveItemCommand(Command):
    def __init__(self, scene, item) -> None:
        self.scene = scene
        self.item = item
        self._is_image = item in scene._image_items

    def do(self) -> None:
        self.scene.removeItem(self.item)
        if self._is_image:
            _sync_images(self.scene, self.item, False)
        self.scene._expand_scene_if_needed()

    def undo(self) -> None:
        if self.item.scene() is None:
            self.scene.addItem(self.item)
        if self._is_image:
            _sync_images(self.scene, self.item, True)
        self.scene._expand_scene_if_needed()


_STYLE_PROPS = ("line_color", "line_width", "fill_color", "fill_alpha")


def capture_state(item) -> dict:
    """Snapshot of everything the user can edit on an item without a tool."""
    state = {"pos": item.pos(), "z": item.zValue()}
    if hasattr(item, "setRect") and hasattr(item, "rect"):
        state["rect"] = item.rect()
    for name in _STYLE_PROPS:
        if hasattr(item, name):
            state[name] = getattr(item, name)()
    if hasattr(item, "restore_geometry"):
        state["geometry"] = item.geometry_state()
    return state


def apply_state(item, state: dict) -> None:
    item.setPos(state["pos"])
    item.setZValue(state["z"])
    if "rect" in state:
        item.setRect(state["rect"])
    for name in _STYLE_PROPS:
        if name in state:
            getattr(item, "set_" + name)(state[name])
    if "geometry" in state:
        item.restore_geometry(*state["geometry"])


class StateCommand(Command):
    """Undoable edit of existing items (move, resize, colour, width, z-order …).

    `changes` holds (item, before, after) triples from capture_state()."""

    def __init__(self, scene, changes) -> None:
        self.scene = scene
        self.changes = list(changes)

    def _apply(self, which: int) -> None:
        for change in self.changes:
            item = change[0]
            apply_state(item, change[which])
        self.scene._expand_scene_if_needed()
        self.scene.update()

    def do(self) -> None:
        self._apply(2)

    def undo(self) -> None:
        self._apply(1)


def snapshot(scene) -> dict:
    """State of every editable item, for diffing after an interaction."""
    return {i: capture_state(i) for i in scene.items() if i is not scene.base_image()}


def push_changes(scene, before: dict) -> bool:
    """Push a StateCommand for items whose state differs from `before`."""
    changes = []
    for item, old in before.items():
        if item.scene() is not scene:
            continue
        new = capture_state(item)
        if new != old:
            changes.append((item, old, new))
    if changes:
        scene.history().push(StateCommand(scene, changes))
    return bool(changes)


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

    def discard_add(self, item) -> None:
        """Forget the AddItemCommand of an item that never became meaningful."""
        self._undo = [c for c in self._undo if not (isinstance(c, AddItemCommand) and c.item is item)]

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()

    def can_undo(self) -> bool:
        return bool(self._undo)

    def can_redo(self) -> bool:
        return bool(self._redo)
