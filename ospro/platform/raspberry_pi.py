""" Raspberry-Pi general-purpose input / output interface """

from ospro import exceptions

# Import raspberry-pi general-purpose input / output interface.
try:
    import RPi.GPIO as GPIO
except ImportError:
    raise exceptions.InvalidPlatformError(
        ' '.join([
            'Invalid platform.',
            'The {raspberry-pi} platform is only available',
            'on ARM-architecture.'
        ])
    )


def Interface():
    """ Represents the Raspberry-Pi general-purpose input / output interface.
    """
    return GPIO
