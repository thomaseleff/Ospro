"""
Information
---------------------------------------------------------------------
Name        : temp_pid.py
Location    : ~/modules/
Author      : Tom Eleff
Published   : 2023-06-25
Revised on  : .

Description
---------------------------------------------------------------------
Runs the temperature PID controller.
"""

# Import modules
import os
import sys
import time
import copy
import utils.utils as utils
import sensors.temp as temp

# Initialize global variables
config = utils.read_config(
    configLoc=os.path.join(
        os.path.join(os.path.dirname(__file__), os.pardir),
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

    # Import sensor modules
    if not config['session']['dev']:
        import RPi.GPIO as GPIO

    # Initialize temperatore sensor
    tSensor = temp.Sensor(
        outputPin=config['tPID']['pin']
    )
    tSensor.initialize(config)

    # Read temperature
    previousTemp = tSensor.read_temp(config)

    # Convert from fahrenheit to celsius
    if config['settings']['scale'] == 'F':
        previousTemp = tSensor.convert_to_c(previousTemp)

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

            # Convert from fahrenheit to celsius
            if config['settings']['scale'] == 'F':
                setPoint = tSensor.convert_to_c(
                    config['tPID']['setPoint']
                )
                deadZoneRange = tSensor.convert_to_c(
                    config['tPID']['deadZoneRange']
                )
                temperature = tSensor.convert_to_c(
                    temperature
                )

            # Avoid unstable temperatures
            if abs(temperature - previousTemp) >= 5:

                # Reset parameters
                currentTime = time.time()
                print('--')
                pass

            # Calculate pulse width modulation
            else:

                # Set max output if temperature is below the dead-zone
                if temperature < int(
                    (setPoint - deadZoneRange)
                ):

                    # Reset parameters
                    previousError = 0
                    integral = 0
                    output = 100
                    currentTime = time.time()

                    # Output parameters
                    print(
                        ', '.join([
                            'Under ',
                            'PWM: %s %%' % (output),
                            'PID: [0.00, 0.00, 0.00]'
                        ])
                    )

                # Set zero output if temperature is above max temperature
                elif temperature >= 115:

                    # Reset parameters
                    previousError = 0
                    integral = 0
                    output = 100
                    currentTime = time.time()

                    # Output parameters
                    print(
                        ', '.join([
                            'Over ',
                            'PWM: %s %%' % (output),
                            'PID: [0.00, 0.00, 0.00]'
                        ])
                    )

                # Calculate output
                else:

                    # Calculate error
                    error = round(setPoint - temperature, 2)

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
                        '%.2f : %.2f, PWM: %s %%, PID: [%.2f, %.2f, %.2f]' % (
                            temperature,
                            setPoint,
                            output,
                            abs(max(pOut, 0)),
                            abs(max(iOut, 0)),
                            abs(max(dOut, 0))
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
            previousTemp = copy.deepcopy(temperature)
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
