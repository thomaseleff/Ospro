"""
Information
---------------------------------------------------------------------
Name        : temp.py
Location    : ~/ospro/sensors

Description
---------------------------------------------------------------------
Contains the temperature sensor classes and functions.
"""

# Import modules
import random
import sys


# Define temperature sensor class
class Controller():

    def __init__(
        self,
        outputPin
    ):
        """
        Variables
        ---------------------------------------------------------------------
        outputPin               = <int> Pin number that identifies the
                                    pulse width modulation pin.

        Description
        ---------------------------------------------------------------------
        Creates an instance of the Controller class.
        """

        # Assign class variables
        self.outputPin = outputPin

    def initialize(
        self,
        config
    ):
        """
        Variables
        ---------------------------------------------------------------------
        config                  = <dict> Dictionary object containing
                                    the application settings

        Description
        ---------------------------------------------------------------------
        Initializes the temperature controller hardware.
        """

        # Import sensor modules
        if not config['session']['dev']:

            import RPi.GPIO as GPIO

            # Define board mode
            if not GPIO.getmode():
                GPIO.setmode(GPIO.BCM)
            elif GPIO.getmode() == 10:
                print('ERROR: Invalid GPIO mode (BOARD).')
                sys.exit()
            else:
                pass

            # Suppress GPIO warnings
            # GPIO.setwarnings(False)

            # Setup GPIO pins
            self.controller = GPIO.PWM(
                self.outputPin,
                600
            )

            # Start the controller
            self.controller.start(0)

        else:
            self.controller = False

    def start(
        self
    ):
        """
        Variables
        ---------------------------------------------------------------------

        Description
        ---------------------------------------------------------------------
        Starts the duty cycle of the temperature controller class.
        """

        # Start the controller
        self.controller.start(0)

    def stop(
        self
    ):
        """
        Variables
        ---------------------------------------------------------------------

        Description
        ---------------------------------------------------------------------
        Stops the duty cycle of the temperature controller class.
        """

        # Stop the controller
        self.controller.stop()

    def update_duty_cycle(
        self,
        output
    ):
        """
        Variables
        ---------------------------------------------------------------------
        output                  = <int> Pulse width modulation output duty
                                    cycle.

        Description
        ---------------------------------------------------------------------
        Changes the duty cycle of the temperature controller class.
        """

        # Update duty cycle
        self.controller.ChangeDutyCycle(output)


class Sensor():

    def __init__(
        self,
        outputPin
    ):
        """
        Variables
        ---------------------------------------------------------------------
        outputPin               = <int> Pin number that identifies the
                                    pulse width modulation pin.

        Description
        ---------------------------------------------------------------------
        Creates an instance of the Sensor class.
        """

        # Assign class variables
        self.outputPin = outputPin
        self.previousTemperature = None

    def initialize(
        self,
        config
    ):
        """
        Variables
        ---------------------------------------------------------------------
        config                  = <dict> Dictionary object containing
                                    the application settings

        Description
        ---------------------------------------------------------------------
        Initializes the temperature sensor hardware.
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
                print('ERROR: Invalid GPIO mode (BOARD).')
                sys.exit()
            else:
                pass

            # Suppress GPIO warnings
            # GPIO.setwarnings(False)

            # Setup GPIO pins
            GPIO.setup(
                self.outputPin,
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
        config
    ):
        """
        Variables
        ---------------------------------------------------------------------
        config                  = <dict> Dictionary object containing
                                    the application settings

        Description
        ---------------------------------------------------------------------
        Returns the water temperature in degrees Celsius.
        """

        if config['session']['dev']:
            temperature = random.randint(
                int(config['tPID']['setPoint'] * 0.95),
                int(config['tPID']['setPoint'] * 1.02)
            )

        else:
            try:
                temperature = round(self.sensor.temperature, 2)

            except RuntimeError:
                if self.previousTemperature is not None:
                    temperature = self.previousTemperature
                else:
                    print('ERROR: Unable to read temperature sensor.')
                    sys.exit()

        # Evaluate error
        if self.previousTemperature is not None:
            if (
                (
                    abs(temperature - self.previousTemperature) >=
                    config['tPID']['error']
                )
            ):
                temperature = self.previousTemperature

        # Update previous temperature
        self.previousTemperature = temperature

        return int(temperature)


def convert_to_c(
    temperature
):
    """
    Variables
    ---------------------------------------------------------------------
    temperature                 = <float> Temperature value in Fahrenheit

    Description
    ---------------------------------------------------------------------
    Converts {temperature} from Fahrenheit to Celsius.
    """

    return int((float(temperature) - 32) * 5 / 9)


def convert_to_f(
    temperature
):
    """
    Variables
    ---------------------------------------------------------------------
    temperature                 = <float> Temperature value in Celsius.

    Description
    ---------------------------------------------------------------------
    Converts {temperature} from Celsius to Fahrenheit.
    """

    return int((float(temperature) * 9 / 5) + 32)
