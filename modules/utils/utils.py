"""
Information
---------------------------------------------------------------------
Name        : utils.py
Location    : ~/modules/utils/
Author      : Tom Eleff
Published   : 2023-05-14
Revised on  : .

Description
---------------------------------------------------------------------
Contains the utility functions necessary for managing configuration,
validation and user-logging.
"""

# Import Modules
import json
import os


# Define Functions
def read_config(
    configLoc
):
    """
    Variables
    ---------------------------------------------------------------------
    configLoc               = <str> Path to ~/config.json that contains
                                the parameters essential to the
                                application.

    Description
    ---------------------------------------------------------------------
    Reads {configLoc} and returns a dictionary object.
    """

    config = {}

    try:
        with open(
            configLoc,
            mode='r'
        ) as file:
            try:
                config = json.load(file)
            except json.decoder.JSONDecodeError:
                config = False
                raise IOError(
                    'ERROR: ~/%s is invalid.' % (os.path.basename(configLoc))
                )
    except FileNotFoundError:
        config = False
        raise FileNotFoundError(
            'ERROR: %s does not exist.' % (configLoc)
        )

    return config


def validate_config(
    config,
    dtype
):
    """
    Variables
    ---------------------------------------------------------------------
    config                  = <dict> Dictionary object that contains the
                                parameters essential to the application.
    dtype                   = <dict> Dictionary object that contains the
                                expected {config} value dtypes.

    Description
    ---------------------------------------------------------------------
    Validates {config} against the dtypes in {dtype}.
    """

    confErrors = {}
    err = False

    for section in config.keys():
        if section not in dtype.keys():
            dtype[section] = {}
            confErrors[section] = {}
        else:
            confErrors[section] = {}

        for key, value in config[section].items():
            if key not in dtype[section].keys():
                confErrors[section][key] = 'No dtype found in ~/dtypes.json.'
                err = True
            else:
                if type(value).__name__ != dtype[section][key]:
                    confErrors[section][key] = (
                        'Invalid dtype. Expected <' +
                        dtype[section][key] + '>.'
                    )
                    err = True
                else:
                    pass

    len0 = max(
        [len(section) for section in confErrors.keys()]
    )
    if err:
        for section in confErrors.keys():
            if len(confErrors[section].keys()) > 0:

                print(
                    'ERROR: The following errors occurred when' +
                    ' validating the [%s] parameters.\n' %
                    (section)
                )

                len1 = max(
                    [len(key) for key in confErrors[section].keys()]
                )
                len2 = max(
                    [len(value) for value in confErrors[section].values()]
                )

                print(
                    "{:<8} {:<{len0}} {:<{len1}} {:<{len2}}".format(
                        '',
                        'Section',
                        'Key',
                        'Error',
                        len0=len0+4,
                        len1=len1+4,
                        len2=len2+4
                    )
                )
                print(
                    "{:<8} {:<{len0}} {:<{len1}} {:<{len2}}".format(
                        '',
                        '-------',
                        '---',
                        '-----',
                        len0=len0+4,
                        len1=len1+4,
                        len2=len2+4
                    )
                )

                for key, value in confErrors[section].items():
                    print(
                        ("{:<8} {:<{len0}} {:<{len1}} {:<{len2}}").format(
                            '',
                            section,
                            key,
                            value,
                            len0=len0+4,
                            len1=len1+4,
                            len2=len2+4
                        )
                    )
                print(
                    '\n'
                )
            else:
                pass
        raise TypeError(
            'ERROR: Validation failed.'
        )
    else:
        print(
            'NOTE: Validation completed successfully.'
        )


def write_config(
    configLoc,
    config
):
    """
    Variables
    ---------------------------------------------------------------------
    configLoc               = <str> Path to output {config}
    config                  = <dict> Dictionary object that contains the
                                parameters essential to the application.

    Description
    ---------------------------------------------------------------------
    Writes the {config} dictionary object to {configLoc}.
    """

    try:
        with open(
            configLoc,
            mode='w+'
        ) as file:
            json.dump(
                config,
                file,
                indent=4
            )
    except FileNotFoundError:
        raise FileNotFoundError(
            'ERROR: %s does not exist.' % (configLoc)
        )
