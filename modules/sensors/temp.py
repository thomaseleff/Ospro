"""
Information
---------------------------------------------------------------------
Name        : temp.py
Location    : ~/modules/sensors/
Author      : Tom Eleff
Published   : 2023-06-25
Revised on  : .

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
            import busio
            import digitalio
            import RPi.GPIO as GPIO
            import adafruit_max31855 as adafruit

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
            spi = busio.SPI(
                board.SCK,
                MOSI=board.MOSI,
                MISO=board.MISO
            )
            cs = digitalio.DigitalInOut(board.D5)
            self.sensor = adafruit.MAX31855(
                spi,
                cs
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
        Returns the water temperature based on config['settings']['scale'].
        """

        if config['session']['dev']:
            temp = random.randint(
                int(config['tPID']['setPoint'] * 0.95),
                int(config['tPID']['setPoint'] * 1.02)
            )

        else:
            try:
                temp = round(self.sensor.temperature, 2)
            except RuntimeError:
                pass

            if config['settings']['scale'] == 'F':
                temp = self.convert_to_f(temp)

        return int(temp)

    def convert_to_c(
        self,
        temp
    ):
        """
        Variables
        ---------------------------------------------------------------------
        temp                    = <float> Temperature value in fahrenheit

        Description
        ---------------------------------------------------------------------
        Converts {temp} from fahrenheit to celsius.
        """

        return float((temp - 32) * 5 / 9)

    def convert_to_f(
        self,
        temp
    ):
        """
        Variables
        ---------------------------------------------------------------------
        temp                    = <float> Temperature value in celsius.

        Description
        ---------------------------------------------------------------------
        Converts {temp} from celsius to fahrenheit.
        """

        return float((temp * 9 / 5) + 32)
