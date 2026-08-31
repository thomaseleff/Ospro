""" Fatal errors """

import errno

# Error number constants
PLATFORM_ERRNO: int = errno.ENXIO   # No such device or address
INTERFACE_ERRNO: int = errno.EIO    # I / O error

FATAL: list = [PLATFORM_ERRNO]
