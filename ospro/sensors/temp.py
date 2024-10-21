""" Temperature sensor-API

Sensor
------
Adafruit MAX31855
- Compatible with K-type thermocouples
- Measures -200°C to +1350°C output in 0.25 degree increments
  - K-type thermocouples typically range from ±2°C to ±6°C in accuracy
- 3.3 to 5v power supply and logic level compliant
"""

import random
from ospro.platform import factory

# Assign the minimum temperature sensor accuracy
#   for the temperature sensor hardware
ACCURACY: int = 3
MIN: int = 0
MAX: int = 600
RANDOM_SEED: int = 93


class Sensor():
    """ A `class` that represents a temperature sensor.

    Parameters
    ----------
    dev: `bool`
        `True` or `False`, whether dev-mode is enabled.
    """

    def __init__(
        self,
        dev: bool
    ):
        """ Creates an instance of the temperature sensor.

        Parameters
        ----------
        dev: `bool`
            `True` or `False`, whether dev-mode is enabled.
        """

        # Assign class variables
        self.dev: bool = dev

        # Load the raspberry-pi platform interface
        _ = factory.load_interface(dev=dev)

        # Import sensor modules
        if not dev:

            import board
            import digitalio
            import adafruit_max31855

            # Initialize sensors
            self.sensor = adafruit_max31855.MAX31855(
                board.SPI(),
                digitalio.DigitalInOut(board.D5)
            )

        else:
            self.sensor = None

    def read(
        self,
        set_point: int = RANDOM_SEED
    ) -> int:
        """ Returns the temperature in degrees Celsius.

        Parameters
        ----------
        set_point: `int`
            The set-point in degrees Celcius of the system.
                Used for generating random temperatures when {dev} = `True`.
        """

        if self.dev:
            temperature = random.randint(
                int(set_point * 0.95),
                int(set_point * 1.02)
            )
        else:
            try:
                temperature = round(self.sensor.temperature, 0)
            except RuntimeError as e:
                raise RuntimeError(e)

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
