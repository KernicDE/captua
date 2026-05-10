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
