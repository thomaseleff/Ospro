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

        # Load the raspberry-pi platform interface
        _ = factory.load_interface(dev=dev)

        # Import sensor modules
        if not dev:

            import board
            import busio
            import adafruit_ads1x15.ads1115 as ADS
            from adafruit_ads1x15.analog_in import AnalogIn

            # Initialize sensors
            ads = ADS.ADS1115(
                busio.I2C(board.SCL, board.SDA),
                address=0x48
            )
            ads.gain = 2 / 3
            self.sensor = AnalogIn(ads, 0)  # channel 0; ADS.P0 dropped in ads1x15 >=5

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
                    int(set_point) - 10 * 10,
                    int(set_point) + 10 * 10
                ) / 10
            )
        else:
            try:

                # ponytail: `.value` returns the raw 16-bit count, matching
                #   legacy `read_adc` at gain 2/3 for the ADS1115; re-tune the
                #   3.0/1750 & 34.0/7.0 constants on-device if psi reads off.
                pressure = round(
                    (3.0 / 1750)
                    * self.sensor.value
                    - (34.0 / 7.0),
                    1
                )
            except RuntimeError as e:
                raise RuntimeError(e)

        return abs(float(pressure))
