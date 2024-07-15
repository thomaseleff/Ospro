"""
Information
---------------------------------------------------------------------
Name        : main.py
Location    : ~/

Description
---------------------------------------------------------------------
Contains initialization functions and runs the Ospro application.
"""

# Import modules
import subprocess
import time
import os
import sys
import ospro.utils.utils as utils

# Initialize global variables
running = True
dirLoc = os.path.abspath(
    os.path.dirname(__file__)
)
execLoc = os.path.abspath(
    sys.executable
)

# Initialize session dictionary
session = {
    'running': running,
    'assetsLoc': os.path.join(
        dirLoc, 'assets'
    ),
    'configLoc': os.path.join(
        dirLoc, 'config'
    ),
    'diagnosticsLoc': os.path.join(
        dirLoc, 'diagnostics'
    ),
    'modulesLoc': dirLoc,
    'controllersLoc': dirLoc,
    'sensorsLoc': os.path.join(
        dirLoc, 'ospro', 'sensors'
    ),
    'utilsLoc': os.path.join(
        dirLoc, 'ospro', 'utils'
    )
}


# Define functions
def initialize(
    session
):
    """
    Variables
    ---------------------------------------------------------------------
    session                 = <dict> Dictionary object containing the
                                parameters essential to the session.

    Description
    ---------------------------------------------------------------------
    Checks for the dashboard, temp_pid and pressure_pid modules. Reads,
    validates and updates ~/config.json and returns the config dictionary
    object.
    """

    # Check dashboard
    if os.path.isfile(
        os.path.join(
            session['modulesLoc'], 'dashboard.py'
        )
    ):
        session['dashboard'] = True

    # Check temperature PID
    if os.path.isfile(
        os.path.join(
            session['controllersLoc'], 'temp_pid.py'
        )
    ) and (session['dashboard']):
        session['tempPID'] = True

    # Check pressure PID
    if os.path.isfile(
        os.path.join(
            session['controllersLoc'], 'pressure_pid.py'
        )
    ) and (session['dashboard']):
        session['pressurePID'] = True

    # Read config
    config = utils.read_config(
        configLoc=os.path.join(
            session['configLoc'], 'config.json'
        )
    )
    config['session'] = {**config['session'], **session}

    # Validate config
    utils.validate_config(
        config,
        utils.read_config(
            configLoc=os.path.join(
                session['configLoc'], 'dtypes.json'
            )
        )
    )

    # Update config with session parameters
    utils.write_config(
        configLoc=os.path.join(
            session['configLoc'], 'config.json'
        ),
        config=config
    )

    return config


def poll(
    app,
    execLoc,
    appLoc
):
    """
    Variables
    ---------------------------------------------------------------------
    app                     = <class> Subprocess object for an
                                application.

    Description
    ---------------------------------------------------------------------
    Checks the status of the application and re-starts it when not
    running.
    """

    if app.poll() is None:
        pass
    elif app.returncode > 0:
        app = subprocess.Popen(
            [execLoc, appLoc]
        )
    else:
        app = False

    return app


# Main
if __name__ == '__main__':

    # Initialize the application
    config = initialize(session)

    # Initialize dashboard
    if config['session']['dashboard']:
        dashboard_app = subprocess.Popen(
            [
                execLoc,
                os.path.join(
                    config['session']['modulesLoc'],
                    'dashboard.py'
                )
            ]
        )

    # Initialize temperature controller
    if config['session']['tempPID']:
        temp_pid_app = subprocess.Popen(
            [
                execLoc,
                os.path.join(
                    config['session']['controllersLoc'],
                    'temp_pid.py'
                )
            ]
        )

    # Initialize pressure controller
    if config['session']['pressurePID']:
        pass
        # pressure_pid_app = subprocess.Popen(
        #     [
        #         execLoc,
        #         os.path.join(
        #             config['session']['controllersLoc'],
        #             'pressure_pid.py'
        #         )
        #     ]
        # )

    while config['session']['running']:

        # Read config
        config = utils.read_config(
            configLoc=os.path.join(
                config['session']['configLoc'],
                'config.json'
            )
        )

        try:
            if dashboard_app:
                dashboard_app = poll(
                    app=dashboard_app,
                    execLoc=execLoc,
                    appLoc=os.path.join(
                        config['session']['modulesLoc'],
                        'dashboard.py'
                    )
                )

                temp_pid_app = poll(
                    app=temp_pid_app,
                    execLoc=execLoc,
                    appLoc=os.path.join(
                        config['session']['controllersLoc'],
                        'temp_pid.py'
                    )
                )

            else:

                # Terminate applications
                config['session']['running'] = False
                utils.write_config(
                    configLoc=os.path.join(
                        session['configLoc'], 'config.json'
                    ),
                    config=config
                )

        except KeyboardInterrupt:

            # Terminate applications
            config['session']['running'] = False
            utils.write_config(
                configLoc=os.path.join(
                    session['configLoc'], 'config.json'
                ),
                config=config
            )

        time.sleep(5)
