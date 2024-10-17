""" Temperature controller and sensor API """

import sys
import random


# Temperature controller
class Controller():
    """ A `class` that represents a temperature controller.

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
        """ Initializes the temperature controller hardware.

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
        """ Starts the duty cycle of the temperature controller.
        """

        # Start the controller
        self.controller.start(0)

    def stop(
        self
    ):
        """ Stops the duty cycle of the temperature controller.
        """

        # Stop the controller
        self.controller.stop()

    def update_duty_cycle(
        self,
        output: float
    ):
        """ Changes the duty cycle of the temperature controller.

        Parameters
        ----------
        output: `float`
            The pulse width modulation output duty cycle.
        """

        # Update duty cycle
        self.controller.ChangeDutyCycle(output)


# Temperature sensor
class Sensor():
    """ A `class` that represents a temperature sensor.

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
        # self.previousTemperature = None

    def initialize(
        self,
        config: dict
    ):
        """ Initializes the temperature sensor hardware.

        Parameters
        ----------
        config: `dict`
            Dictionary object containing the application settings.
        """

        # Import sensor modules
        if not config['session']['dev']:

            import board
            import digitalio
            import RPi.GPIO as GPIO
            import adafruit_max31855

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
            self.sensor = adafruit_max31855.MAX31855(
                board.SPI(),
                digitalio.DigitalInOut(board.D5)
            )
        else:
            self.sensor = False

    def read_temp(
        self,
        config: dict
    ) -> int:
        """ Returns the temperature in degrees Celsius.

        Parameters
        ----------
        config: `dict`
            Dictionary object containing the application settings.
        """

        if config['session']['dev']:
            temperature = random.randint(
                int(config['tPID']['setPoint'] * 0.95),
                int(config['tPID']['setPoint'] * 1.02)
            )

        else:
            try:
                temperature = round(self.sensor.temperature, 2)

            except RuntimeError as e:
                raise RuntimeError(e)

        #         if self.previousTemperature is not None:
        #             temperature = self.previousTemperature
        #         else:
        #             print('ERROR: Unable to read temperature sensor.')
        #             sys.exit()

        # # Evaluate error
        # if self.previousTemperature is not None:
        #     if (
        #         (
        #             abs(temperature - self.previousTemperature) >=
        #             config['tPID']['error']
        #         )
        #     ):
        #         temperature = self.previousTemperature

        # # Update previous temperature
        # self.previousTemperature = temperature

        return int(temperature)


def convert_to_c(
    temperature: float
) -> int:
    """ Converts {temperature} from Fahrenheit to Celsius.

    Parameters
    ----------
    temperature: `float`
        Temperature value in Fahrenheit.
    """

    return int((float(temperature) - 32) * 5 / 9)


def convert_to_f(
    temperature: float
) -> int:
    """ Converts {temperature} from Celsius to Fahrenheit.

    Parameters
    ----------
    temperature: `float`
        Temperature value in Celsius.
    """

    return int((float(temperature) * 9 / 5) + 32)
