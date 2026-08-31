""" Temperature controller-API """

from ospro.controllers import _controller


class Controller(_controller.GenericController):
    """ A `class` that represents a temperature controller.

    Parameters
    ----------
    dev: `bool`
        `True` or `False`, whether dev-mode is enabled.
    output_pin: `int`
        Pin number that identifies the pulse width modulation pin.
    """
    pass
