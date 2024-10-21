""" Other (mocked) general-purpose input / output interface """

from typing import Union, Dict
from ospro.platform._interface import AbstractInterface
from ospro.platform._interface import Pin
from ospro.platform._interface import Controller


class Interface(AbstractInterface):
    """ Other (mocked) general-purpose input / output interface """

    def __init__(self):
        self.channels: Dict[str, Pin] = {}

    def setup(
        self,
        channel: int,
        mode: int,
        pull_up_down: int = AbstractInterface.PUD_OFF
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
        self.channels[channel] = Pin(
            mode=mode,
            pull_up_down=pull_up_down
        )

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
        if channel in self.channels[channel]:
            _pin = Pin(
                mode=self.channels[channel].mode,
                pull_up_down=self.channels[channel].pull_up_down,
                value=value
            )
        else:
            _pin = Pin(
                value=value
            )
        self.channels[channel] = _pin

    def input(self, pin) -> Union[int, bool]:
        """ Reads the specified pin and returns HIGH/true if the pin is pulled
        high, or LOW/false if pulled low.

        Parameters
        ----------
        channel: `int`
            A general-purpose input/output pin that is enabled
                during espresso extraction.
        """
        return self.channels.get(pin, None)

    def cleanup(self, channel: Union[int, None] = None):
        """ Cleans up GPIO event detection for specific pin, or all pins if
        `None` is specified.

        Parameters
        ----------
        channel: `Union[int, None]`
            A general-purpose input/output pin.
        """
        if channel:
            del self.channels[channel]
        else:
            self.channels.clear()

    class PWM(AbstractInterface.AbstractPWM):
        """ Represents pulse-width modulation. """

        def __init__(
            self,
            channel: int,
            frequency: float
        ):
            """ Creates an instance of the pulse-width modulation controller.

            Parameters
            ----------
            channel: `int`
                A general-purpose input/output pin.
            frequency: `int`
                The frequency of the pulse-width modulation.
            """
            self.channel: int = channel
            self.controller = Controller(
                dutycycle=self.OFF,
                pwm=True,
                frequency=frequency
            )

        def start(self, dutycycle: float):
            """ Starts the controller.

            Parameters
            ----------
            dutycycle: `float`
                The pulse width modulation output duty cycle.
            """
            self.controller.dutycycle = dutycycle

        def ChangeDutyCycle(self, dutycycle: float):
            """ Changes the duty cycle of the controller.

            Parameters
            ----------
            dutycycle: `float`
                The pulse width modulation output duty cycle.
            """
            self.controller.dutycycle = dutycycle

        def stop(self):
            """ Stops the controller. """
            self.controller.dutycycle = 0
