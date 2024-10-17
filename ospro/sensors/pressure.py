""" Pressure controller and sensor API """

import sys
import random


# Pressure controller
class Controller():
    """ A `class` that represents a pressure controller.

    Parameters
    ----------
    output_pin: `int`
        Pin number that identifies the pulse width modulation pin.
    """

    def __init__(
        self,
        output_pin: int
    ):
        """ Creates an instance of the Controller class.

        Parameters
        ----------
        output_pin: `int`
            Pin number that identifies the pulse width modulation pin.
        """

        # Assign class variables
        self.output_pin: int = output_pin

    def initialize(
        self,
        config: dict
    ):
        """ Initializes the pressure controller hardware.

        Parameters
        ----------
        config: `dict`
            Dictionary object containing the application settings.
        """

        # Import sensor modules
        if not config['session']['dev']:

            import RPi.GPIO as GPIO

            # Define board mode
            if not GPIO.getmode():
                GPIO.setmode(GPIO.BCM)
            elif GPIO.getmode() == 10:
                print('ERROR: Invalid GPIO mode {BOARD}.')
                sys.exit()
            else:
                pass

            # Suppress GPIO warnings
            # GPIO.setwarnings(False)

            # Setup GPIO pins
            self.controller = GPIO.PWM(
                self.output_pin,
                600
            )

            # Start the controller
            self.controller.start(0)

        else:
            self.controller = False

    def start(
        self
    ):
        """ Starts the duty cycle of the pressure controller.
        """

        # Start the controller
        self.controller.start(0)

    def stop(
        self
    ):
        """ Stops the duty cycle of the pressure controller.
        """

        # Stop the controller
        self.controller.stop()

    def update_duty_cycle(
        self,
        output: float
    ):
        """ Changes the duty cycle of the pressure controller.

        Parameters
        ----------
        output: `float`
            The pulse width modulation output duty cycle.
        """

        # Update duty cycle
        self.controller.ChangeDutyCycle(output)


# Pressure sensor
class Sensor():
    """ A `class` that represents a pressure sensor.

    Parameters
    ----------
    output_pin: `int`
        Pin number that identifies the pulse width modulation pin.
    """

    def __init__(
        self,
        output_pin: int
    ):
        """ Creates an instance of the Sensor class.

        Parameters
        ----------
        output_pin: `int`
            Pin number that identifies the pulse width modulation pin.
        """

        # Assign class variables
        self.output_pin: int = output_pin

    def initialize(
        self,
        config: dict
    ):
        """ Initializes the pressure sensor hardware.

        Parameters
        ----------
        config: `dict`
            Dictionary object containing the application settings.
        """

        # Import sensor modules
        if not config['session']['dev']:

            import RPi.GPIO as GPIO
            import Adafruit_ADS1x15 as adafruit

            # Define board mode
            if not GPIO.getmode():
                GPIO.setmode(GPIO.BCM)
            elif GPIO.getmode() == 10:
                print('ERROR: Invalid GPIO mode {BOARD}.')
                sys.exit()
            else:
                pass

            # Suppress GPIO warnings
            # GPIO.setwarnings(False)

            # Setup GPIO pins
            GPIO.setup(
                self.output_pin,
                GPIO.OUT
            )

            # Initialize sensors
            self.sensor = adafruit.ADS1115(
                address=0x48,
                busnum=1
            )
        else:
            self.sensor = False

    def read_pressure(
        self,
        config: dict
    ) -> float:
        """ Returns the pressure in bars.

        Parameters
        ----------
        config: `dict`
            Dictionary object containing the application settings.
        """

        if config['session']['dev']:
            pressure = float(random.randint(80, 90) / 10)
        else:
            try:
                pressure = round(
                    (3.0 / 1750) *
                    (self.sensor.read_adc(
                        0,
                        gain=2 / 3
                    )) - (34.0 / 7.0), 1
                )
            except RuntimeError as e:
                raise RuntimeError(e)

        return float(pressure)
