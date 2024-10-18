""" Ospro """

from typing import Union
import os
import sys
import time
import subprocess
from ospro import logging
from pytensils import config

# Initialize global variables
RUNNING: bool = True
DIR_NAME: Union[str, os.PathLike] = os.path.abspath(
    os.path.dirname(__file__)
)
EXECUTABLE: Union[str, os.PathLike] = os.path.abspath(sys.executable)
SESSION: dict = {
    'running': RUNNING,
    'assetsLoc': os.path.join(
        DIR_NAME, 'assets'
    ),
    'configLoc': os.path.join(
        DIR_NAME, 'config'
    ),
    'diagnosticsLoc': os.path.join(
        DIR_NAME, 'diagnostics'
    ),
    'modulesLoc': DIR_NAME,
    'controllersLoc': DIR_NAME,
    'sensorsLoc': os.path.join(
        DIR_NAME, 'ospro', 'sensors'
    ),
    'utilsLoc': os.path.join(
        DIR_NAME, 'ospro', 'utils'
    )
}


# Define app-orchestration functions
def initialize(
    session_object: dict,
    Logging: logging.Logger
) -> config.Handler:
    """ Checks for the dashboard, temp_pid and pressure_pid modules. Reads,
    validates and updates ~/config.json and returns a
    `pytensils.config.Handler` object.

    Parameters
    ----------
    session_object: `dict`
        Dictionary object containing the parameters essential to the session.
    Logging: `logging.Logger`
        Logging object for debug console logging.
    """

    # Check dashboard
    if os.path.isfile(
        os.path.join(
            session_object['modulesLoc'], 'dashboard.py'
        )
    ):
        session_object['dashboard'] = True

    # Check temperature PID
    if os.path.isfile(
        os.path.join(
            session_object['controllersLoc'], 'temp_pid.py'
        )
    ) and (session_object['dashboard']):
        session_object['tempPID'] = True

    # Check pressure PID
    if os.path.isfile(
        os.path.join(
            session_object['controllersLoc'], 'pressure_pid.py'
        )
    ) and (session_object['dashboard']):
        session_object['pressurePID'] = True

    # Read config
    Config = config.Handler(path=os.path.join(session_object['configLoc']))
    Config.data['session'] = {**Config.data['session'], **session_object}

    # Validate config
    if Config.validate(
        dtypes=config.Handler(
            path=os.path.join(session_object['configLoc']),
            file_name='dtypes.json'
        ).to_dict()
    ):

        # Logging
        Logging.debug('NOTE: Config validation completed successfully.')

        # Update config with session parameters
        Config.write()

    return Config


def poll(
    app: subprocess.Popen,
    executable_path: Union[str, os.PathLike],
    app_path: Union[str, os.PathLike]
):
    """ Checks the status of the application and re-starts it when not
    running.

    Parameters
    ----------
    app: `subprocess.Popen`
        Class instance of the application.
    executable_path: `Union[str, os.PathLike]`
        The local file-path of the Python executable.
    app_path: `Union[str, os.PathLike]`
        The local file-path of the application entrypoint.
    """

    if app.poll() is None:
        pass
    elif app.returncode > 0:

        # Restart
        app = subprocess.Popen([executable_path, app_path])

        # Logging
        Logging.debug(
            'NOTE: {%s} restarted successfully.' % (os.path.basename(app_path))
        )

    else:
        app = False

    return app


if __name__ == '__main__':

    # Setup logging
    Logging = logging.get_ospro_logger()

    # Initialize the application
    Config = initialize(session_object=SESSION, Logging=Logging)

    # Initialize the dashboard-UI
    if Config.data['session']['dashboard']:
        dashboard_app = subprocess.Popen(
            [
                EXECUTABLE,
                os.path.join(
                    Config.data['session']['modulesLoc'],
                    'dashboard.py'
                )
            ]
        )

    # Initialize the temperature controller
    if Config.data['session']['tempPID']:
        temp_pid_app = subprocess.Popen(
            [
                EXECUTABLE,
                os.path.join(
                    Config.data['session']['controllersLoc'],
                    'temp_pid.py'
                )
            ]
        )

    # Initialize the pressure controller
    if Config.data['session']['pressurePID']:
        pass
        # pressure_pid_app = subprocess.Popen(
        #     [
        #         EXECUTABLE,
        #         os.path.join(
        #             Config.data['session']['controllersLoc'],
        #             'pressure_pid.py'
        #         )
        #     ]
        # )

    while Config.data['session']['running']:

        # Read config
        Config = config.Handler(
            path=os.path.join(
                Config.data['session']['configLoc']
            )
        )

        try:
            if dashboard_app:
                dashboard_app = poll(
                    app=dashboard_app,
                    executable_path=EXECUTABLE,
                    app_path=os.path.join(
                        Config.data['session']['modulesLoc'],
                        'dashboard.py'
                    )
                )

                temp_pid_app = poll(
                    app=temp_pid_app,
                    executable_path=EXECUTABLE,
                    app_path=os.path.join(
                        Config.data['session']['controllersLoc'],
                        'temp_pid.py'
                    )
                )

            else:

                # Terminate applications
                Config.data['session']['running'] = False
                Config.write()

        except KeyboardInterrupt:

            # Terminate applications
            Config.data['session']['running'] = False
            Config.write()

        time.sleep(5)
