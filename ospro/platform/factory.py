""" Platform factory """

import platform
from ospro import exceptions

TYPES = {
    'raspberry-pi': 'raspberry-pi',
    'other': 'other'
}


def load_interface(
    dev: bool
):
    """ Loads the platform interface.

    Parameters
    ----------
    dev: `bool`
        `True` or `False`, whether dev-mode is enabled.
    """

    # Parse platform
    machine_platform = parse_platform(dev=dev)

    # Raise an exception if an invalid platform is assigned
    if machine_platform.strip().lower() not in list(TYPES.values()):
        raise exceptions.InvalidPlatformError(
            'Invalid platform. The available platforms are [%s]' % (
                ', '.join(list(TYPES.values()))
            )
        )

    # Raise an exception if the raspberry-pi platform is requested when
    #   running on non-ARM architecture
    if (
        machine_platform.strip().lower() == TYPES['raspberry-pi']
        and (
            platform.system() != 'Linux'
            or 'arm' not in platform.machine()
        )
    ):
        raise exceptions.InvalidPlatformError(
            ' '.join([
                'Invalid platform.',
                'The {raspberry-pi} platform is only available',
                'on ARM-architecture.'
            ])
        )

    # Configure the raspberry-pi platform
    if machine_platform.strip().lower() == TYPES['raspberry-pi']:
        from ospro.platform import raspberry_pi
        return raspberry_pi.Interface()

    # Skip configuration for all other platforms
    if machine_platform.strip().lower() == TYPES['other']:
        from ospro.platform import other
        return other.Interface()


def parse_platform(dev: bool):
    """ Parses the platform from the execution mode.

    Parameters
    ----------
    dev: `bool`
        `True` or `False`, whether dev-mode is enabled.
    """
    if dev:
        return TYPES['other']
    else:
        return TYPES['raspberry-pi']
