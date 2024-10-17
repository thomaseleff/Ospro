""" Temperature PID-controller """

import os
import sys
import time
import copy
import errno
import logging
from pytensils import config
from ospro.sensors import temp

if __name__ == '__main__':

    # Setup logging
    Logging = logging.getLogger('temp-pid')
    Logging.setLevel(level=logging.DEBUG)
    debugger = logging.StreamHandler()
    debugger.setLevel(level=logging.DEBUG)
    debugger.setFormatter(
        fmt=logging.Formatter('\033[94m[tPID ] %(message)s\033[0m')
    )
    Logging.addHandler(hdlr=debugger)

    # Load configuration
    Config = config.Handler(
        path=os.path.join(
            os.path.dirname(__file__),
            'config'
        )
    )

    # Validate configuration
    Dtypes = config.Handler(
        path=os.path.join(
            os.path.dirname(__file__),
            'config'
        ),
        file_name='dtypes.json'
    )

    if Config.validate(
        dtypes=config.Handler(
            path=os.path.join(
                os.path.dirname(__file__),
                'config'
            ),
            file_name='dtypes.json'
        ).to_dict()
    ):

        # Logging
        Logging.debug('NOTE: Config validation completed successfully.')

        # Update config
        configuration = Config.to_dict()

    # Configure environment
    if not configuration['session']['dev']:

        # Import GPIO module
        import RPi.GPIO as GPIO

        # Define board mode
        if not GPIO.getmode():
            GPIO.setmode(GPIO.BCM)
        elif GPIO.getmode() == 10:
            Logging.error('ERROR: Invalid GPIO mode {BOARD}.')
            sys.exit()
        else:
            pass

        # Suppress GPIO warnings
        # GPIO.setwarnings(False)

        # Setup GPIO pins
        GPIO.setup(
            configuration['extraction']['pin'],
            GPIO.IN,
            pull_up_down=GPIO.PUD_DOWN
        )

    # Initialize temperatore sensor
    tSensor = temp.Sensor(
        output_pin=configuration['tPID']['pin']
    )
    tSensor.initialize(config=configuration)

    # Read temperature
    previous_temperature = tSensor.read_temp(config=configuration)

    # Set initial parameters
    previous_time = time.time()
    integral = 0
    previous_error = 0

    # Set intitial pulse width modulation output
    if not configuration['session']['dev']:
        tController = temp.Controller(
            output_pin=configuration['tPID']['pin']
        )
        tController.initialize(config=configuration)
        tController.start()

    # Startup delay
    time.sleep(0.001)

    # Run
    while configuration['session']['running']:

        # Read config
        configuration = Config.read()

        # Catch keyboard interrupt
        try:

            # Read temperature
            try:
                temperature = tSensor.read_temp(config=configuration)
            except RuntimeError:
                sys.exit(errno.EIO)

            # Pass if temperature is unstable
            if (
                (
                    abs(temperature - previous_temperature) >=
                    configuration['tPID']['error']
                )
            ):

                # Pass
                # previous_error = 0
                # integral = 0
                # output = 0
                current_time = time.time()
                Logging.debug(
                    "{:<{len0}} {:<{len1}} {:<{len2}} {:<{len3}}".format(
                        'Status: Pass',
                        'Temp: (%.2f, %.2f)' % (
                            temperature,
                            configuration['tPID']['setPoint']
                        ),
                        'PWM: N/A',
                        'PID: [-.--, -.--, -.--]',
                        len0=17,
                        len1=26,
                        len2=14,
                        len3=26
                    )
                )

            # Set full output if temperature is below the dead-zone
            elif temperature < int(
                (
                    configuration['tPID']['setPoint'] -
                    configuration['tPID']['deadZoneRange']
                )
            ):

                # Reset parameters
                previous_error = 0
                integral = 0
                output = 100
                current_time = time.time()

                # Output parameters
                Logging.debug(
                    "{:<{len0}} {:<{len1}} {:<{len2}} {:<{len3}}".format(
                        'Status: Under',
                        'Temp: (%.2f, %.2f)' % (
                            temperature,
                            configuration['tPID']['setPoint']
                        ),
                        'PWM: %s %%' % (output),
                        'PID: [%.2f, %.2f, %.2f]' % (
                            0,
                            0,
                            0
                        ),
                        len0=17,
                        len1=26,
                        len2=14,
                        len3=26
                    )
                )

            # Set zero output if temperature is above the set-point
            elif temperature >= configuration['tPID']['setPoint']:

                # Reset parameters
                previous_error = 0
                integral = 0
                output = 0
                current_time = time.time()

                # Output parameters
                Logging.debug(
                    "{:<{len0}} {:<{len1}} {:<{len2}} {:<{len3}}".format(
                        'Status: Over',
                        'Temp: (%.2f, %.2f)' % (
                            temperature,
                            configuration['tPID']['setPoint']
                        ),
                        'PWM: %s %%' % (output),
                        'PID: [%.2f, %.2f, %.2f]' % (
                            0,
                            0,
                            0
                        ),
                        len0=17,
                        len1=26,
                        len2=14,
                        len3=26
                    )
                )

            # Calculate output
            else:

                # Calculate error
                error = round(
                    configuration['tPID']['setPoint'] - temperature,
                    2
                )

                # Calculate proportional output
                p_out = configuration['tPID']['p'] * error

                # Calculate integral output
                current_time = time.time()
                delta_time = current_time - previous_time
                integral += (error * delta_time)
                i_out = (configuration['tPID']['i'] * integral)

                # Calculate derivative output
                delta_error = error - previous_error
                derivative = (delta_error/delta_time)
                d_out = (configuration['tPID']['d'] * derivative)

                output = max(min(int(p_out + i_out + d_out), 100), 0)

                # Output parameters
                Logging.debug(
                    "{:<{len0}} {:<{len1}} {:<{len2}} {:<{len3}}".format(
                        'Status: Valid',
                        'Temp: (%.2f, %.2f)' % (
                            temperature,
                            configuration['tPID']['setPoint']
                        ),
                        'PWM: %s %%' % (output),
                        'PID: [%.2f, %.2f, %.2f]' % (
                            abs(max(p_out, 0)),
                            abs(max(i_out, 0)),
                            abs(max(d_out, 0))
                        ),
                        len0=17,
                        len1=26,
                        len2=14,
                        len3=26
                    )
                )

            # Set pulse width modulation output
            if not configuration['session']['dev']:

                # Set default during extraction
                if GPIO.input(
                    configuration['extraction']['pin']
                ):
                    output = 10

                # Update duty cycle
                tController.update_duty_cycle(output)

            # Recalculate time delta for delay
            delta_time = (time.time() - previous_time)

            # Update parameters
            previous_temperature = copy.deepcopy(temperature)
            previous_time = copy.deepcopy(current_time)

            # Delay
            time.sleep(configuration['tPID']['sampleRate'])

        except KeyboardInterrupt:

            # Terminate pulse width modulation & cleanup
            if not configuration['session']['dev']:
                tController.stop()
                GPIO.cleanup()

            # Exit
            sys.exit()

    # Terminate pulse width modulation & cleanup
    if not configuration['session']['dev']:
        tController.stop()
        GPIO.cleanup()
