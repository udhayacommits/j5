"""Tests for the Piezo Classes."""

from datetime import timedelta
from typing import List, Optional, Type

import pytest

from j5.boards import Board
from j5.components.piezo import Note, Piezo, PiezoInterface


class MockPiezoDriver(PiezoInterface):
    """A testing driver for the piezo."""

    def buzz(self, identifier: int,
             duration: timedelta, frequency: int) -> None:
        """Queue a pitch to be played."""
        pass


class MockPiezoBoard(Board):
    """A testing board for the piezo."""

    @property
    def name(self) -> str:
        """The name of this board."""
        return "Mock Piezo Board"

    @property
    def serial(self) -> str:
        """The serial number of this board."""
        return "SERIAL"

    @property
    def firmware_version(self) -> Optional[str]:
        """Get the firmware version of this board."""
        return self._backend.get_firmware_version()

    @staticmethod
    def supported_components() -> List[Type['Component']]:
        """List the components that this Board supports."""
        return [Piezo]

    def make_safe(self) -> None:
        """Make this board safe."""
        pass


def test_piezo_interface_implementation() -> None:
    """Test that we can implement the PiezoInterface."""
    MockPiezoDriver()


def test_piezo_instantiation() -> None:
    """Test that we can instantiate an piezo."""
    Piezo(0, MockPiezoBoard(), MockPiezoDriver())


def test_piezo_interface_class_method() -> None:
    """Tests piezo's interface_class method."""
    piezo = Piezo(0, MockPiezoBoard(), MockPiezoDriver())
    assert piezo.interface_class() is PiezoInterface


def test_piezo_buzz_method() -> None:
    """Tests piezo's buzz method's input validation."""
    piezo = Piezo(0, MockPiezoBoard(), MockPiezoDriver())
    piezo.buzz(timedelta(seconds=1), 2093)
    piezo.buzz(timedelta(minutes=1), Note.D7)


def test_piezo_buzz_invalid_value() -> None:
    """Test piezo's buzz method's input validation."""
    piezo = Piezo(0, MockPiezoBoard(), MockPiezoDriver())
    with pytest.raises(ValueError):
        piezo.buzz(timedelta(seconds=1), -42)
    with pytest.raises(TypeError):
        piezo.buzz(timedelta(seconds=1), "j5")
    with pytest.raises(ValueError):
        piezo.buzz(timedelta(seconds=-2), Note.D7)
    with pytest.raises(TypeError):
        piezo.buzz(1, Note.D7)


def test_note_reversed() -> None:
    """Test Note reversed dunder method."""
    assert list(reversed(list(Note))) == list(reversed(Note))
