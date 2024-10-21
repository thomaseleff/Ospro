""" Abstract general-purpose input / output interface """

from typing import Union
from abc import ABC, abstractmethod
from dataclasses import dataclass


class AbstractInterface(ABC):
    """ Abstract general-purpose input / output interface. """

    # Interface constants
    OUT: int = 0
    IN: int = 1
    HIGH: bool = True
    LOW: bool = False

    RISING: int = 1
    FALLING: int = 2
    BOTH: int = 3

    PUD_OFF: int = 0
    PUD_DOWN: int = 1
    PUD_UP: int = 2

    @abstractmethod
    def setup(
        self,
        channel: int,
        mode: int,
        pull_up_down: int = PUD_OFF
    ):
        """ Sets the input or output mode for a specified pin.  Mode should be
        either OUT or IN.

        Parameters
        ----------
        channel: `int`
            A general-purpose input/output pin.
        mode: `int`
            Either OUT or IN.
        pull_up_down: `int`
            Either PUD_OFF, PUD_DOWN or PUD_UP.
        """
        raise NotImplementedError

    @abstractmethod
    def output(self, channel: int, value: Union[int, bool]):
        """ Sets the specified pin the provided high/low value.  Value should
        be either HIGH/LOW or a boolean (true = high).

        Parameters
        ----------
        channel: `int`
            A general-purpose input/output pin.
        value: `Union[int, bool]`
            Either HIGH or LOW or True (HIGH) or False (LOW).
        """
        raise NotImplementedError

    @abstractmethod
    def input(self, channel: int):
        """ Reads the specified pin and return HIGH/true if the pin is pulled
        high, or LOW/false if pulled low.

        Parameters
        ----------
        channel: `int`
            A general-purpose input/output pin that is enabled
                during espresso extraction.
        """
        raise NotImplementedError

    @abstractmethod
    def cleanup(self, channel: Union[int, None] = None):
        """ Cleans up GPIO event detection for specific pin, or all pins if
        `None` is specified.

        Parameters
        ----------
        channel: `Union[int, None]`
            A general-purpose input/output pin.
        """
        raise NotImplementedError

    class AbstractPWM(ABC):
        """ Abstract pulse-width modulation controller. """

        # Controller constants
        OFF: int = 0
        ON: int = 1

        @abstractmethod
        def __init__(self, channel: int, frequency: float):
            """ Creates an instance of the pulse-width modulation controller.

            Parameters
            ----------
            channel: `int`
                A general-purpose input/output pin.
            frequency: `int`
                The frequency of the pulse-width modulation.
            """
            raise NotImplementedError

        @abstractmethod
        def start(self):
            """ Starts the controller. """
            raise NotImplementedError

        @abstractmethod
        def stop(self):
            """ Stops the controller. """
            raise NotImplementedError


@dataclass
class Pin():
    """ Represents a general-pupose input / output pin. """

    mode: Union[int, None] = None
    pull_up_down: Union[int, None] = None
    value: Union[int, bool, None] = None


@dataclass
class Controller():
    """ Represents a general-pupose input / output pin controller. """

    dutycycle: Union[int, bool] = False
    pwm: Union[bool] = False
    frequency: Union[float, None] = None
