""" Generic controller """

from ospro.platform import factory


class GenericController():
    """ A `class` that represents a generic controller.

    Parameters
    ----------
    dev: `bool`
        `True` or `False`, whether dev-mode is enabled.
    output_pin: `int`
        Pin number that identifies the pulse width modulation pin.
    """

    def __init__(
        self,
        dev: bool,
        output_pin: int
    ):
        """ Creates an instance of the controller.

        Parameters
        ----------
        dev: `bool`
            `True` or `False`, whether dev-mode is enabled.
        output_pin: `int`
            The general-purpose input/output pin that sets the
                pulse-width power output for the controller.
        """

        # Assign class variables
        self.output_pin: int = output_pin

        # Load the platform interface
        GPIO = factory.load_interface(dev=dev)

        # Setup the platform interface for the controller
        GPIO.setup(
            self.output_pin,
            GPIO.OUT
        )

        # Create a pulse-width modulation controller
        self.controller = GPIO.PWM(
            self.output_pin,
            600
        )

        # Start the controller
        self.controller.start(0)

    def start(
        self
    ):
        """ Starts the duty cycle of the controller. """
        self.controller.start(0)

    def stop(
        self
    ):
        """ Stops the duty cycle of the controller. """
        self.controller.stop()

    def update_duty_cycle(
        self,
        output: float
    ):
        """ Changes the duty cycle of the controller.

        Parameters
        ----------
        output: `float`
            The pulse-width modulation output duty cycle.
        """
        self.controller.ChangeDutyCycle(output)
