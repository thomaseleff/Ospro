""" Temperature PID-controller """

import os
import sys
import time
import copy
from pytensils import config
from ospro import logging, exceptions, errors
from ospro.platform import factory
from ospro.sensors import temp as ts
from ospro.controllers import temp as tc

if __name__ == '__main__':

    # Setup logging
    Logging = logging.get_temperature_pid_logger()

    # Load configuration
    Config = config.Handler(
        path=os.path.join(
            os.path.dirname(__file__),
            'config'
        )
    )

    # Validate configuration
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

    # Load the platform interface
    try:
        GPIO = factory.load_interface(
            dev=Config.data['session']['dev']
        )
    except exceptions.InvalidPlatformError:
        sys.exit(errors.PLATFORM_ERRNO)

    # Setup the interface
    GPIO.setup(
        Config.data['extraction']['pin'],
        GPIO.IN,
        pull_up_down=GPIO.PUD_DOWN
    )

    # Initialize temperatore sensor
    tSensor = ts.Sensor(dev=Config.data['session']['dev'])

    # Read temperature
    previous_temperature = tSensor.read(
        set_point=Config.data['tPID']['setPoint']
    )

    # Set initial parameters
    previous_time = time.time()
    integral = 0
    previous_error = 0

    # Set intitial pulse-width modulation output
    tController = tc.Controller(
        dev=Config.data['session']['dev'],
        output_pin=Config.data['tPID']['pin']
    )

    # Startup delay
    time.sleep(0.001)

    # Catch keyboard interrupt
    try:

        # Run
        while Config.data['session']['running']:

            # Read config
            Config.data = Config.read()

            # Read temperature
            try:
                temperature = tSensor.read(
                    set_point=Config.data['tPID']['setPoint']
                )
            except RuntimeError:
                sys.exit(errors.INTERFACE_ERRNO)

            # Pass if temperature is unstable
            if (
                (
                    abs(temperature - previous_temperature)
                    >= Config.data['tPID']['error']
                )
            ):

                # Pass
                # previous_error = 0
                # integral = 0
                # output = 0
                current_time = time.time()
                Logging.debug(
                    "{:<{len0}}  {:<{len1}}  {:<{len2}}  {:<{len3}}".format(
                        'Status: Pass',
                        'Temp: (%3.0f, %3.0f)' % (
                            temperature,
                            Config.data['tPID']['setPoint']
                        ),
                        'PWM: N/A',
                        'PID: [-.--, -.--, -.--]',
                        len0=13,
                        len1=16,
                        len2=10,
                        len3=22
                    )
                )

            # Set full output if temperature is below the dead-zone
            elif temperature < int(
                (
                    Config.data['tPID']['setPoint']
                    - Config.data['tPID']['deadZoneRange']
                )
            ):

                # Reset parameters
                previous_error = 0
                integral = 0
                output = 100
                current_time = time.time()

                # Logging
                Logging.debug(
                    "{:<{len0}}  {:<{len1}}  {:<{len2}}  {:<{len3}}".format(
                        'Status: Under',
                        'Temp: (%3.0f, %3.0f)' % (
                            temperature,
                            Config.data['tPID']['setPoint']
                        ),
                        'PWM: %3.0f %%' % (output),
                        'PID: [%.2f, %.2f, %.2f]' % (
                            0,
                            0,
                            0
                        ),
                        len0=13,
                        len1=16,
                        len2=10,
                        len3=22
                    )
                )

            # Set zero output if temperature is above the set-point
            elif temperature >= int(
                Config.data['tPID']['setPoint']
                + ts.ACCURACY
            ):

                # Reset parameters
                previous_error = 0
                integral = 0
                output = 0
                current_time = time.time()

                # Logging
                Logging.debug(
                    "{:<{len0}}  {:<{len1}}  {:<{len2}}  {:<{len3}}".format(
                        'Status: Over',
                        'Temp: (%3.0f, %3.0f)' % (
                            temperature,
                            Config.data['tPID']['setPoint']
                        ),
                        'PWM: %3.0f %%' % (output),
                        'PID: [%.2f, %.2f, %.2f]' % (
                            0,
                            0,
                            0
                        ),
                        len0=13,
                        len1=16,
                        len2=10,
                        len3=22
                    )
                )

            # Calculate output
            else:

                # Calculate error
                error = round(
                    Config.data['tPID']['setPoint'] - temperature,
                    2
                )

                # Calculate the proportional output
                p_out = Config.data['tPID']['p'] * error

                # Calculate the integral output
                current_time = time.time()
                delta_time = current_time - previous_time
                integral += (error * delta_time)
                i_out = (Config.data['tPID']['i'] * integral)

                # Calculate the derivative output
                delta_error = error - previous_error
                derivative = (delta_error / delta_time)
                d_out = (Config.data['tPID']['d'] * derivative)

                # Calculate the total output
                output = max(min(int(p_out + i_out + d_out), 100), 0)

                # Logging
                Logging.debug(
                    "{:<{len0}}  {:<{len1}}  {:<{len2}}  {:<{len3}}".format(
                        'Status: Valid',
                        'Temp: (%3.0f, %3.0f)' % (
                            temperature,
                            Config.data['tPID']['setPoint']
                        ),
                        'PWM: %3.0f %%' % (output),
                        'PID: [%.2f, %.2f, %.2f]' % (
                            abs(max(p_out, 0)),
                            abs(max(i_out, 0)),
                            abs(max(d_out, 0))
                        ),
                        len0=13,
                        len1=16,
                        len2=10,
                        len3=22
                    )
                )

            # Set default during extraction
            if GPIO.input(Config.data['extraction']['pin']):
                output = 10

            # Update the duty-cycle
            tController.update_duty_cycle(output)

            # Recalculate time delta for delay
            delta_time = (time.time() - previous_time)

            # Update parameters
            previous_temperature = copy.deepcopy(temperature)
            previous_time = copy.deepcopy(current_time)

            # Delay
            time.sleep(Config.data['tPID']['sampleRate'])

    except KeyboardInterrupt:

        # Terminate pulse-width modulation & cleanup
        tController.stop()
        GPIO.cleanup()

        # Exit
        sys.exit()

    # Terminate pulse-width modulation & cleanup
    tController.stop()
    GPIO.cleanup()
