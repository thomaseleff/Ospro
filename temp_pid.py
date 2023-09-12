"""
Information
---------------------------------------------------------------------
Name        : temp_pid.py
Location    : ~/
Author      : Tom Eleff
Published   : 2023-06-25
Revised on  : 2023-07-07

Description
---------------------------------------------------------------------
Runs the temperature PID controller.
"""

# Import modules
import os
import sys
import time
import copy
import ospro.utils.utils as utils
import ospro.sensors.temp as temp

# Initialize global variables
config = utils.read_config(
    configLoc=os.path.join(
        os.path.dirname(__file__),
        'config',
        'config.json'
    )
)

# Configure environment
if not config['session']['dev']:

    # Import GPIO module
    import RPi.GPIO as GPIO

    # Define board mode
    if not GPIO.getmode():
        GPIO.setmode(GPIO.BCM)
    elif GPIO.getmode() == 10:
        print('ERROR: Invalid GPIO mode (BOARD).')
        sys.exit()
    else:
        pass

    # Suppress GPIO warnings
    # GPIO.setwarnings(False)

    # Setup GPIO pins
    GPIO.setup(
        config['extraction']['pin'],
        GPIO.IN,
        pull_up_down=GPIO.PUD_DOWN
    )

# Main
if __name__ == '__main__':

    # Initialize temperatore sensor
    tSensor = temp.Sensor(
        outputPin=config['tPID']['pin']
    )
    tSensor.initialize(config)

    # Read temperature
    previousTemperature = tSensor.read_temp(config)

    # Set initial parameters
    previousTime = time.time()
    integral = 0
    previousError = 0

    # Set intitial pulse width modulation output
    if not config['session']['dev']:
        tController = temp.Controller(
            outputPin=config['tPID']['pin']
        )
        tController.initialize(config)
        tController.start()

    # Startup delay
    time.sleep(0.001)

    # Run
    while config['session']['running']:

        # Read config
        config = utils.read_config(
            configLoc=os.path.join(
                config['session']['configLoc'],
                'config.json'
            )
        )

        try:

            # Read temperature
            temperature = tSensor.read_temp(config)

            # Avoid unstable temperatures
            if (
                (
                    abs(temperature - previousTemperature) >=
                    config['tPID']['error']
                )
            ):

                # Reset parameters
                currentTime = time.time()
                print(
                    "{:<{len0}} {:<{len1}} {:<{len2}} {:<{len3}}".format(
                        'Status: Reset',
                        'Temp: (%.2f, %.2f)' % (
                            temperature,
                            config['tPID']['setPoint']
                        ),
                        'PWM: N/A',
                        'PID: [-.--, -.--, -.--]',
                        len0=17,
                        len1=26,
                        len2=14,
                        len3=26
                    )
                )

            # Calculate pulse width modulation
            else:

                # Set max output if temperature is below the dead-zone
                if temperature < int(
                    (
                        config['tPID']['setPoint'] -
                        config['tPID']['deadZoneRange']
                    )
                ):

                    # Reset parameters
                    previousError = 0
                    integral = 0
                    output = 100
                    currentTime = time.time()

                    # Output parameters
                    print(
                        "{:<{len0}} {:<{len1}} {:<{len2}} {:<{len3}}".format(
                            'Status: Under',
                            'Temp: (%.2f, %.2f)' % (
                                temperature,
                                config['tPID']['setPoint']
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

                # Set zero output if temperature is above max temperature
                elif temperature >= 115:

                    # Reset parameters
                    previousError = 0
                    integral = 0
                    output = 0
                    currentTime = time.time()

                    # Output parameters
                    print(
                        "{:<{len0}} {:<{len1}} {:<{len2}} {:<{len3}}".format(
                            'Status: Over',
                            'Temp: (%.2f, %.2f)' % (
                                temperature,
                                config['tPID']['setPoint']
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
                    error = round(config['tPID']['setPoint'] - temperature, 2)

                    # Calculate proportional output
                    pOut = config['tPID']['p'] * error

                    # Calculate integral output
                    currentTime = time.time()
                    deltaTime = currentTime - previousTime
                    integral += (error * deltaTime)
                    iOut = (config['tPID']['i'] * integral)

                    # Calculate derivative output
                    deltaError = error - previousError
                    derivative = (deltaError/deltaTime)
                    dOut = (config['tPID']['d'] * derivative)

                    output = max(min(int(pOut + iOut + dOut), 100), 0)

                    # Output parameters
                    print(
                        "{:<{len0}} {:<{len1}} {:<{len2}} {:<{len3}}".format(
                            'Status: Valid',
                            'Temp: (%.2f, %.2f)' % (
                                temperature,
                                config['tPID']['setPoint']
                            ),
                            'PWM: %s %%' % (output),
                            'PID: [%.2f, %.2f, %.2f]' % (
                                abs(max(pOut, 0)),
                                abs(max(iOut, 0)),
                                abs(max(dOut, 0))
                            ),
                            len0=17,
                            len1=26,
                            len2=14,
                            len3=26
                        )
                    )

            # Set pulse width modulation output
            if not config['session']['dev']:

                # Set default during extraction
                if GPIO.input(
                    config['extraction']['pin']
                ):
                    output = 10

                # Update duty cycle
                tController.update_duty_cycle(output)

            # Recalculate time delta for delay
            deltaTime = (time.time() - previousTime)

            # Update parameters
            previousTemperature = copy.deepcopy(temperature)
            previousTime = copy.deepcopy(currentTime)

            # Delay
            time.sleep(config['tPID']['sampleRate'])

        except KeyboardInterrupt:

            # Terminate pulse width modulation & cleanup
            if not config['session']['dev']:
                tController.stop()
                GPIO.cleanup()

            # Exit
            sys.exit()

    # Terminate pulse width modulation & cleanup
    if not config['session']['dev']:
        tController.stop()
        GPIO.cleanup()
