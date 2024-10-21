""" Pressure sensor-API

Sensor
------
Pressure transducer 1/8 IN NPT thread stainless steel (500 PSI)
- Measures 0 to 500 psi output in 1 psi increments
  - ±0.5% psi in accuracy
- 5v power supply and logic level compliant
- 0.5v - 4.5v linear voltage output,
  - 0 psi outputs 0.5v
  - 500 psi outputs 4.5v
"""

import random
from ospro.platform import factory

# Assign the minimum pressure sensor accuracy
#   for the pressure sensor hardware
ACCURACY: float = 0.344738
MIN: int = 0
MAX: int = 500
RANDOM_SEED: int = 9


class Sensor():
    """ A `class` that represents a pressure sensor.

    Parameters
    ----------
    dev: `bool`
        `True` or `False`, whether dev-mode is enabled.
    """

    def __init__(
        self,
        dev: bool
    ):
        """ Creates an instance of the pressure sensor.

        Parameters
        ----------
        dev: `bool`
            `True` or `False`, whether dev-mode is enabled.
        """

        # Assign class variables
        self.dev: bool = dev

        # Import sensor modules
        if not dev:

            import Adafruit_ADS1x15 as adafruit

            # Load the raspberry-pi platform interface
            _ = factory.load_interface(dev=dev)

            # Initialize sensors
            self.sensor = adafruit.ADS1115(
                address=0x48,
                busnum=1
            )

        else:
            self.sensor = None

    def read(
        self,
        set_point: int = RANDOM_SEED
    ) -> float:
        """ Returns the pressure in bars.

        Parameters
        ----------
        set_point: `int`
            The set-point in bars of the system.
                Used for generating random pressure values when {dev} = `True`.
        """

        if self.dev:
            pressure = float(
                random.randint(
                    set_point - 10 * 10,
                    set_point + 10 * 10
                ) / 10
            )
        else:
            try:
                pressure = round(
                    (3.0 / 1750)
                    * (
                        self.sensor.read_adc(
                            0,
                            gain=2 / 3
                        )
                    )
                    - (34.0 / 7.0),
                    1
                )
            except RuntimeError as e:
                raise RuntimeError(e)

        return abs(float(pressure))
