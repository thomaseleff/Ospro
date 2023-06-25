"""
Information
---------------------------------------------------------------------
Name        : pressure.py
Location    : ~/modules/sensors/
Author      : Tom Eleff
Published   : 2023-06-25
Revised on  : .

Description
---------------------------------------------------------------------
Contains the pressure sensor classes and functions.
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
        Initializes the pressure controller hardware.
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
        Starts the duty cycle of the pressure controller class.
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
        Stops the duty cycle of the pressure controller class.
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
        Changes the duty cycle of the pressure controller class.
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
        Initializes the pressure sensor hardware.
        """

        # Import sensor modules
        if not config['session']['dev']:

            import RPi.GPIO as GPIO
            import Adafruit_ADS1x15 as adafruit

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
            self.sensor = adafruit.ADS1115(
                address=0x48,
                busnum=1
            )
        else:
            self.sensor = False

    def read_pressure(
        self,
        config
    ):
        """
        Variables
        ---------------------------------------------------------------------

        Description
        ---------------------------------------------------------------------
        Returns the system pressure.
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
            except RuntimeError:
                pass

        return pressure
