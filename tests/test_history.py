"""Tests for History undo/redo stack."""
import pytest
from captua.history import AddItemCommand, Command, History, RemoveItemCommand


class _FakeScene:
    def __init__(self):
        self.items_added = []
        self.items_removed = []

    def addItem(self, item) -> None:
        self.items_added.append(item)

    def removeItem(self, item) -> None:
        self.items_removed.append(item)


class _FakeItem:
    def __init__(self, name: str = "item"):
        self._name = name
        self._scene = None

    def scene(self):
        return self._scene


def test_push_calls_do():
    executed = []

    class _Cmd(Command):
        def do(self) -> None:
            executed.append("do")

    h = History()
    h.push(_Cmd())
    assert executed == ["do"]


def test_undo_calls_undo_and_removes_from_stack():
    undone = []

    class _Cmd(Command):
        def do(self) -> None:
            pass

        def undo(self) -> None:
            undone.append("undo")

    h = History()
    h.push(_Cmd())
    assert h.can_undo()
    h.undo()
    assert undone == ["undo"]
    assert not h.can_undo()


def test_redo_after_undo():
    log = []

    class _Cmd(Command):
        def do(self) -> None:
            log.append("do")

        def undo(self) -> None:
            log.append("undo")

    h = History()
    h.push(_Cmd())
    h.undo()
    assert h.can_redo()
    h.redo()
    assert log == ["do", "undo", "do"]
    assert not h.can_redo()


def test_push_clears_redo_stack():
    log = []

    class _Cmd(Command):
        def do(self) -> None:
            log.append("do")

        def undo(self) -> None:
            pass

    h = History()
    h.push(_Cmd())
    h.undo()
    assert h.can_redo()
    h.push(_Cmd())  # new action should wipe redo
    assert not h.can_redo()


def test_clear_empties_both_stacks():
    class _Cmd(Command):
        def do(self) -> None:
            pass

        def undo(self) -> None:
            pass

    h = History()
    h.push(_Cmd())
    h.push(_Cmd())
    h.undo()
    h.clear()
    assert not h.can_undo()
    assert not h.can_redo()


def test_undo_empty_is_noop():
    h = History()
    h.undo()  # should not raise


def test_redo_empty_is_noop():
    h = History()
    h.redo()  # should not raise


def test_add_item_command():
    scene = _FakeScene()
    item = _FakeItem()
    cmd = AddItemCommand(scene, item)
    cmd.do()
    assert item in scene.items_added
    cmd.undo()
    assert item in scene.items_removed


def test_remove_item_command():
    scene = _FakeScene()
    item = _FakeItem()
    # Simulate item already in scene
    scene.items_added.append(item)
    cmd = RemoveItemCommand(scene, item)
    cmd.do()
    assert item in scene.items_removed
    cmd.undo()
    assert scene.items_added.count(item) == 2  # added again on undo
