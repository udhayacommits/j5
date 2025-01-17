"""Tests for the SourceBots Arduino hardware implementation."""

from datetime import timedelta
from math import isclose
from typing import Optional, cast

import pytest
from tests.backends.hardware.j5.mock_serial import MockSerial

from j5.backends import CommunicationError
from j5.backends.hardware.env import NotSupportedByHardwareError
from j5.backends.hardware.sb.arduino import SBArduinoHardwareBackend
from j5.components import GPIOPinMode


class SBArduinoSerial(MockSerial):
    """SBArduinoSerial is the same as MockSerial, but includes expected received data."""

    expected_baudrate = 115200
    firmware_version = "2019.6.0"

    def __init__(self,
                 port: Optional[str] = None,
                 baudrate: int = 9600,
                 bytesize: int = 8,
                 parity: str = 'N',
                 stopbits: float = 1,
                 timeout: Optional[float] = None,
                 ):
        super().__init__(
            port=port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            timeout=timeout,
        )
        self.append_received_data(b"# Booted", newline=True)
        version_line = b"# SBDuino GPIO v" + self.firmware_version.encode("utf-8")
        self.append_received_data(version_line, newline=True)

    def respond_to_write(self, data: bytes) -> None:
        """Hook that can be overriden by subclasses to respond to sent data."""
        self.append_received_data(b"+ OK", newline=True)

    def check_data_sent_by_constructor(self) -> None:
        """Check that the backend constructor sent expected data to the serial port."""
        data = "".join(f"W {i} Z\n" for i in range(2, 14))
        self.check_sent_data(data.encode("utf-8"))


class SBArduinoSerialOldVersion1(SBArduinoSerial):
    """Like SBArduinoSerial, but reports an older version number."""

    firmware_version = "2018.7.0"


class SBArduinoSerialOldVersion2(SBArduinoSerial):
    """Like SBArduinoSerial, but reports an older version number."""

    firmware_version = "2019.5.0"


class SBArduinoSerialNewVersion1(SBArduinoSerial):
    """Like SBArduinoSerial, but reports an newer version number."""

    firmware_version = "2019.6.1"


class SBArduinoSerialNewVersion2(SBArduinoSerial):
    """Like SBArduinoSerial, but reports an newer version number."""

    firmware_version = "2019.7.0"


class SBArduinoSerialNewVersion3(SBArduinoSerial):
    """Like SBArduinoSerial, but reports an newer version number."""

    firmware_version = "2020.1.0"


class SBArduinoSerialFailureResponse(SBArduinoSerial):
    """Like SBArduinoSerial, but returns a failure response rather than success."""

    def respond_to_write(self, data: bytes) -> None:
        """Hook that can be overriden by subclasses to respond to sent data."""
        self.append_received_data(b"- Something went wrong", newline=True)


def test_backend_initialisation() -> None:
    """Test that we can initialise a SBArduinoHardwareBackend."""
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    assert type(backend) is SBArduinoHardwareBackend
    assert type(backend._serial) is SBArduinoSerial
    assert all(
        pin.mode is GPIOPinMode.DIGITAL_INPUT for pin in backend._digital_pins.values()
    )
    assert all(pin.state is False for pin in backend._digital_pins.values())


def test_backend_initialisation_serial() -> None:
    """Test commands/responses are sent/received during initialisation."""
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    serial = cast(SBArduinoSerial, backend._serial)
    serial.check_data_sent_by_constructor()
    serial.check_all_received_data_consumed()


def test_backend_version_check() -> None:
    """Test that an exception is raised if the arduino reports an unsupported version."""
    with pytest.raises(CommunicationError):
        SBArduinoHardwareBackend("COM0", SBArduinoSerialOldVersion1)
    with pytest.raises(CommunicationError):
        SBArduinoHardwareBackend("COM0", SBArduinoSerialOldVersion2)
    SBArduinoHardwareBackend("COM0", SBArduinoSerialNewVersion1)
    SBArduinoHardwareBackend("COM0", SBArduinoSerialNewVersion2)
    SBArduinoHardwareBackend("COM0", SBArduinoSerialNewVersion3)


def test_backend_firmware_version() -> None:
    """Test that the firmware version is parsed correctly."""
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    assert backend.firmware_version == SBArduinoSerial.firmware_version


def test_backend_handles_failure() -> None:
    """Test that an exception is raised when a failure response is received."""
    with pytest.raises(CommunicationError):
        SBArduinoHardwareBackend("COM0", SBArduinoSerialFailureResponse)


def test_backend_get_set_pin_mode() -> None:
    """Test that we can get and set pin modes."""
    pin = 2
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    assert backend.get_gpio_pin_mode(pin) is GPIOPinMode.DIGITAL_INPUT
    backend.set_gpio_pin_mode(pin, GPIOPinMode.DIGITAL_OUTPUT)
    assert backend.get_gpio_pin_mode(pin) is GPIOPinMode.DIGITAL_OUTPUT


def test_backend_digital_pin_modes() -> None:
    """Test that only certain modes are valid on digital pins."""
    pin = 2
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    backend.set_gpio_pin_mode(pin, GPIOPinMode.DIGITAL_INPUT)
    backend.set_gpio_pin_mode(pin, GPIOPinMode.DIGITAL_INPUT_PULLUP)
    with pytest.raises(NotSupportedByHardwareError):
        backend.set_gpio_pin_mode(pin, GPIOPinMode.DIGITAL_INPUT_PULLDOWN)
    backend.set_gpio_pin_mode(pin, GPIOPinMode.DIGITAL_OUTPUT)
    with pytest.raises(NotSupportedByHardwareError):
        backend.set_gpio_pin_mode(pin, GPIOPinMode.ANALOGUE_INPUT)
    with pytest.raises(NotSupportedByHardwareError):
        backend.set_gpio_pin_mode(pin, GPIOPinMode.ANALOGUE_OUTPUT)
    with pytest.raises(NotSupportedByHardwareError):
        backend.set_gpio_pin_mode(pin, GPIOPinMode.PWM_OUTPUT)


def test_backend_analogue_pin_modes() -> None:
    """Test that only certain modes are valid on digital pins."""
    pin = 14
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    with pytest.raises(NotSupportedByHardwareError):
        backend.set_gpio_pin_mode(pin, GPIOPinMode.DIGITAL_INPUT)
    with pytest.raises(NotSupportedByHardwareError):
        backend.set_gpio_pin_mode(pin, GPIOPinMode.DIGITAL_INPUT_PULLUP)
    with pytest.raises(NotSupportedByHardwareError):
        backend.set_gpio_pin_mode(pin, GPIOPinMode.DIGITAL_INPUT_PULLDOWN)
    with pytest.raises(NotSupportedByHardwareError):
        backend.set_gpio_pin_mode(pin, GPIOPinMode.DIGITAL_OUTPUT)
    backend.set_gpio_pin_mode(pin, GPIOPinMode.ANALOGUE_INPUT)
    with pytest.raises(NotSupportedByHardwareError):
        backend.set_gpio_pin_mode(pin, GPIOPinMode.ANALOGUE_OUTPUT)
    with pytest.raises(NotSupportedByHardwareError):
        backend.set_gpio_pin_mode(pin, GPIOPinMode.PWM_OUTPUT)


def test_backend_write_digital_state() -> None:
    """Test that we can write the digital state of a pin."""
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    serial = cast(SBArduinoSerial, backend._serial)
    serial.check_data_sent_by_constructor()
    # This should put the pin into the most recent (or default) output state.
    backend.set_gpio_pin_mode(2, GPIOPinMode.DIGITAL_OUTPUT)
    serial.check_sent_data(b"W 2 L\n")
    backend.write_gpio_pin_digital_state(2, True)
    serial.check_sent_data(b"W 2 H\n")
    backend.write_gpio_pin_digital_state(2, False)
    serial.check_sent_data(b"W 2 L\n")
    serial.check_all_received_data_consumed()


def test_backend_write_digital_state_requires_pin_mode() -> None:
    """Check that pin must be in DIGITAL_OUTPUT mode for write digital state to work."""
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    assert backend.get_gpio_pin_mode(2) is not GPIOPinMode.DIGITAL_OUTPUT
    with pytest.raises(ValueError):
        backend.write_gpio_pin_digital_state(2, True)


def test_backend_write_digital_state_requires_digital_pin() -> None:
    """Check that pins 14-19 are not supported by write digital state."""
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    with pytest.raises(NotSupportedByHardwareError):
        backend.write_gpio_pin_digital_state(14, True)


def test_backend_digital_state_persists() -> None:
    """Test switching to a different mode and then back to output."""
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    serial = cast(SBArduinoSerial, backend._serial)
    serial.check_data_sent_by_constructor()
    backend.set_gpio_pin_mode(2, GPIOPinMode.DIGITAL_OUTPUT)
    serial.check_sent_data(b"W 2 L\n")
    backend.write_gpio_pin_digital_state(2, True)
    serial.check_sent_data(b"W 2 H\n")
    backend.set_gpio_pin_mode(2, GPIOPinMode.DIGITAL_INPUT)
    serial.check_sent_data(b"W 2 Z\n")
    backend.set_gpio_pin_mode(2, GPIOPinMode.DIGITAL_OUTPUT)
    serial.check_sent_data(b"W 2 H\n")
    backend.write_gpio_pin_digital_state(2, False)
    serial.check_sent_data(b"W 2 L\n")
    backend.set_gpio_pin_mode(2, GPIOPinMode.DIGITAL_INPUT)
    serial.check_sent_data(b"W 2 Z\n")
    backend.set_gpio_pin_mode(2, GPIOPinMode.DIGITAL_OUTPUT)
    serial.check_sent_data(b"W 2 L\n")
    serial.check_all_received_data_consumed()


def test_backend_get_digital_state() -> None:
    """Test that we can read back the digital state of a pin."""
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    # This should put the pin into the most recent (or default) output state.
    backend.set_gpio_pin_mode(2, GPIOPinMode.DIGITAL_OUTPUT)
    assert backend.get_gpio_pin_digital_state(2) is False
    backend.write_gpio_pin_digital_state(2, True)
    assert backend.get_gpio_pin_digital_state(2) is True
    backend.write_gpio_pin_digital_state(2, False)
    assert backend.get_gpio_pin_digital_state(2) is False


def test_backend_get_digital_state_requires_pin_mode() -> None:
    """Check that pin must be in DIGITAL_OUTPUT mode for get digital state to work."""
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    assert backend.get_gpio_pin_mode(2) is not GPIOPinMode.DIGITAL_OUTPUT
    with pytest.raises(ValueError):
        backend.get_gpio_pin_digital_state(2)


def test_backend_get_digital_state_requires_digital_pin() -> None:
    """Check that pins 14-19 are not supported by get digital state."""
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    with pytest.raises(NotSupportedByHardwareError):
        backend.get_gpio_pin_digital_state(14)


def test_backend_input_modes() -> None:
    """Check that the correct commands are send when setting pins to input modes."""
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    serial = cast(SBArduinoSerial, backend._serial)
    serial.check_data_sent_by_constructor()
    backend.set_gpio_pin_mode(2, GPIOPinMode.DIGITAL_INPUT)
    serial.check_sent_data(b"W 2 Z\n")
    backend.set_gpio_pin_mode(2, GPIOPinMode.DIGITAL_INPUT_PULLUP)
    serial.check_sent_data(b"W 2 P\n")
    with pytest.raises(NotSupportedByHardwareError):
        backend.set_gpio_pin_mode(2, GPIOPinMode.DIGITAL_INPUT_PULLDOWN)
    serial.check_all_received_data_consumed()


def test_backend_read_digital_state() -> None:
    """Test that we can read the digital state of a pin."""
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    serial = cast(SBArduinoSerial, backend._serial)
    serial.check_data_sent_by_constructor()

    backend.set_gpio_pin_mode(2, GPIOPinMode.DIGITAL_INPUT)
    serial.check_sent_data(b"W 2 Z\n")

    serial.append_received_data(b"> H", newline=True)
    assert backend.read_gpio_pin_digital_state(2) is True
    serial.check_sent_data(b"R 2\n")

    serial.append_received_data(b"> L", newline=True)
    assert backend.read_gpio_pin_digital_state(2) is False
    serial.check_sent_data(b"R 2\n")

    serial.append_received_data(b"> X", newline=True)  # invalid
    with pytest.raises(CommunicationError):
        backend.read_gpio_pin_digital_state(2)
    serial.check_sent_data(b"R 2\n")

    serial.check_all_received_data_consumed()


def test_backend_read_digital_state_requires_pin_mode() -> None:
    """Check that pin must be in DIGITAL_INPUT* mode for read digital state to work."""
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    backend.set_gpio_pin_mode(2, GPIOPinMode.DIGITAL_OUTPUT)
    assert backend.get_gpio_pin_mode(2) is not GPIOPinMode.DIGITAL_INPUT
    with pytest.raises(ValueError):
        backend.read_gpio_pin_digital_state(2)


def test_backend_read_digital_state_requires_digital_pin() -> None:
    """Check that pins 14-19 are not supported by read digital state."""
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    with pytest.raises(NotSupportedByHardwareError):
        backend.read_gpio_pin_digital_state(14)


def test_backend_read_analogue() -> None:
    """Test that we can read the digital state of a pin."""
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    serial = cast(SBArduinoSerial, backend._serial)
    serial.check_data_sent_by_constructor()

    readings = [212, 535, 662, 385]
    for i, expected_reading in enumerate(readings):
        # "read analogue" command reads all four pins at once.
        identifier = 14 + i
        for j, reading in enumerate(readings):
            serial.append_received_data(f"> a{j} {reading}".encode("utf-8"), newline=True)
        expected_voltage = (expected_reading / 1024.0) * 5.0
        measured_voltage = backend.read_gpio_pin_analogue_value(identifier)
        assert isclose(measured_voltage, expected_voltage)
        serial.check_sent_data(b"A\n")

    serial.check_all_received_data_consumed()


def test_backend_read_analogue_requires_analogue_pin() -> None:
    """Check that pins 2-13 are not supported by read analogue."""
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    with pytest.raises(NotSupportedByHardwareError):
        backend.read_gpio_pin_analogue_value(13)


def test_ultrasound_pulse() -> None:
    """Test that we can read an ultrasound pulse time."""
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    serial = cast(SBArduinoSerial, backend._serial)
    serial.check_data_sent_by_constructor()

    serial.append_received_data(b"> 2345\n")
    duration = backend.get_ultrasound_pulse(3, 4)
    serial.check_sent_data(b"T 3 4\n")
    assert duration == timedelta(microseconds=2345)

    # Check backend updated its view of what modes the pins are in now.
    assert backend.get_gpio_pin_mode(3) is GPIOPinMode.DIGITAL_OUTPUT
    assert backend.get_gpio_pin_digital_state(3) is False
    assert backend.get_gpio_pin_mode(4) is GPIOPinMode.DIGITAL_INPUT

    serial.check_all_received_data_consumed()


def test_ultrasound_pulse_on_same_pin() -> None:
    """Test same pin for trigger and echo."""
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    serial = cast(SBArduinoSerial, backend._serial)
    serial.check_data_sent_by_constructor()

    serial.append_received_data(b"> 2345\n")
    duration = backend.get_ultrasound_pulse(3, 3)
    serial.check_sent_data(b"T 3 3\n")
    assert duration == timedelta(microseconds=2345)

    # Check backend updated its view of what modes the pins are in now.
    assert backend.get_gpio_pin_mode(3) is GPIOPinMode.DIGITAL_INPUT

    serial.check_all_received_data_consumed()


def test_ultrasound_pulse_timeout() -> None:
    """Test that None is returned upon a timeout occurring."""
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    serial = cast(SBArduinoSerial, backend._serial)
    serial.check_data_sent_by_constructor()

    serial.append_received_data(b"> 0\n")
    duration = backend.get_ultrasound_pulse(3, 4)
    serial.check_sent_data(b"T 3 4\n")
    assert duration is None

    serial.check_all_received_data_consumed()


def test_ultrasound_distance() -> None:
    """Test that we can read an ultrasound distance."""
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    serial = cast(SBArduinoSerial, backend._serial)
    serial.check_data_sent_by_constructor()

    serial.append_received_data(b"> 1230\n")
    metres = backend.get_ultrasound_distance(3, 4)
    serial.check_sent_data(b"U 3 4\n")
    assert metres is not None
    assert isclose(metres, 1.23)

    # Check backend updated its view of what modes the pins are in now.
    assert backend.get_gpio_pin_mode(3) is GPIOPinMode.DIGITAL_OUTPUT
    assert backend.get_gpio_pin_digital_state(3) is False
    assert backend.get_gpio_pin_mode(4) is GPIOPinMode.DIGITAL_INPUT

    serial.check_all_received_data_consumed()


def test_ultrasound_distance_on_same_pin() -> None:
    """Test same pin for trigger and echo."""
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    serial = cast(SBArduinoSerial, backend._serial)
    serial.check_data_sent_by_constructor()

    serial.append_received_data(b"> 1230\n")
    metres = backend.get_ultrasound_distance(3, 3)
    serial.check_sent_data(b"U 3 3\n")
    assert metres is not None
    assert isclose(metres, 1.23)

    # Check backend updated its view of what modes the pins are in now.
    assert backend.get_gpio_pin_mode(3) is GPIOPinMode.DIGITAL_INPUT

    serial.check_all_received_data_consumed()


def test_ultrasound_distance_timeout() -> None:
    """Test that None is returned upon a timeout occurring."""
    backend = SBArduinoHardwareBackend("COM0", SBArduinoSerial)
    serial = cast(SBArduinoSerial, backend._serial)
    serial.check_data_sent_by_constructor()

    serial.append_received_data(b"> 0\n")
    metres = backend.get_ultrasound_distance(3, 4)
    serial.check_sent_data(b"U 3 4\n")
    assert metres is None

    serial.check_all_received_data_consumed()
