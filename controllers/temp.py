import time
import os
import copy
import board
import busio
import digitalio
import RPi.GPIO as GPIO
import adafruit_max31855 as AdaT

# Define Board Mode
GPIO.setmode(GPIO.BCM)

# Define LED Pin Numbers
# ledRed = 14
# ledGreen = 15
# ledBlue = 18
pinPwm = 12
pinBrew = 15

# Set LED Pin Mode
# GPIO.setup(ledRed, GPIO.OUT)
# GPIO.setup(ledGreen, GPIO.OUT)
# GPIO.setup(ledBlue, GPIO.OUT)
GPIO.setup(
    pinPwm,
    GPIO.OUT
)
GPIO.setup(
    pinBrew,
    GPIO.IN,
    pull_up_down=GPIO.PUD_DOWN
)

# --------------------------------------------------
# Assign Global Variables and Import Configuration
# --------------------------------------------------

# Define Global Variables
targetError = 0.5
configDict = {}
applicationLoc = os.path.dirname(
    os.path.dirname(__file__)
)
dirSep = '/'

# --------------------------------------------------
# Initialize Sensors
# --------------------------------------------------

spi = busio.SPI(
    board.SCK,
    MOSI=board.MOSI,
    MISO=board.MISO
)
cs = digitalio.DigitalInOut(board.D5)
Amp = AdaT.MAX31855(
    spi,
    cs
)

# --------------------------------------------------
# Define Functions
# --------------------------------------------------


def readConfig():
    global configDict, setPoint, deadZoneRange, sample, kP, kI, kD

    # Import Configs and Store Dictionaries
    if os.path.isfile(
        applicationLoc + dirSep +
        'config' + dirSep + 'config.txt'
    ):
        with open(
            applicationLoc + dirSep +
            'config' + dirSep + 'config.txt'
        ) as file:
            for line in file:
                (var, val) = line.split('|')
                try:
                    configDict[var] = int(val)
                except ValueError:
                    configDict[var] = str(val).strip('\n')
                if configDict[var] == 'nan':
                    print('ERROR: Missing Value Assignment for config Variable ['+var+'].\
                        Please Provide Correct Value Assignment for ['+var+']\
                        within the config.')
                    exit()
    else:
        print('ERROR: Improper config File Location Provided.')
        print('       Please Provide Real Directory Path for config File.')
        exit()

    # Assign PID Gain Values
    if configDict['scale'].split(' ')[1] == '[F]':
        setPoint = round((configDict['setPoint'] - 32) * 5 / 9, 2)
    else:
        setPoint = configDict['setPoint']

    deadZoneRange = configDict['deadZoneRange']
    sample = configDict['sampleRate']
    kP = float(configDict['gainsPID'].split(',')[0])
    kI = float(configDict['gainsPID'].split(',')[1])
    kD = float(configDict['gainsPID'].split(',')[2])


def read_temp():
    global configDict

    try:
        temp = round(Amp.temperature, 2)
    except RuntimeError:
        pass

    return temp


# --------------------------------------------------
# PID Control
# --------------------------------------------------

# Set Initial LED
# GPIO.output(ledRed, GPIO.LOW)
# GPIO.output(ledGreen, GPIO.LOW)
# GPIO.output(ledBlue, GPIO.HIGH)

# Set Initial Parameters
previousTemp = read_temp()
previousTime = time.time()
integral = 0
previousError = 0

# Set Intitial PWM Output
outPwm = GPIO.PWM(
    pinPwm,
    600
)
outPwm.start(0)

while True:
    try:
        # Read config Params
        readConfig()

        # Read Temperature
        temp = read_temp()

        # Set LED
        # if temp < int(setPoint - targetError):
        #     GPIO.output(ledRed, GPIO.LOW)
        #     GPIO.output(ledGreen, GPIO.LOW)
        #     GPIO.output(ledBlue, GPIO.HIGH)
        # elif temp > int(setPoint + targetError):
        #     GPIO.output(ledRed, GPIO.HIGH)
        #     GPIO.output(ledGreen, GPIO.LOW)
        #     GPIO.output(ledBlue, GPIO.LOW)
        # else:
        #     GPIO.output(ledRed, GPIO.LOW)
        #     GPIO.output(ledGreen, GPIO.HIGH)
        #     GPIO.output(ledBlue, GPIO.LOW)

        # Control Response
        if abs(temp - previousTemp) >= 5:
            print('[Passing to Avoid Signal Noise]')
            pass

        else:
            if temp < int(setPoint - deadZoneRange):

                # Reset Initial Parameters
                previousError = 0
                integral = 0
                targetPwm = 100
                previousTime = time.time()

                # Output PWM Parameters
                print(
                    'Deadzone     , PWM: %s %%, PID: [0.00, 0.00, 0.00]' % (
                        targetPwm
                    )
                )

            elif temp >= 115:

                # Reset Initial Values
                previousError = 0
                integral = 0
                targetPwm = 100
                previousTime = time.time()

                # Output PWM Parameters
                print(
                    'Overheating  , PWM: %s %%, PID: [0.00, 0.00, 0.00]' % (
                        targetPwm
                    )
                )

            else:

                # Calculate System Error
                error = round(setPoint - temp, 2)

                # Calculate Proportional Output
                pOut = kP * error

                # Calculate Integral Output
                currentTime = time.time()
                deltaTime = currentTime - previousTime
                integral += (error * deltaTime)
                iOut = (kI * integral)

                # Calculate Derivative Output
                deltaError = error - previousError
                derivative = (deltaError/deltaTime)
                dOut = (kD * derivative)

                targetPwm = max(min(int(pOut + iOut + dOut), 100), 0)

                # Update previousTime
                previousTime = copy.deepcopy(currentTime)

                # Output PWM Parameters
                print(
                    '%.2f : %.2f, PWM: %s %%, PID: [%.2f, %.2f, %.2f]' % (
                        temp,
                        setPoint,
                        targetPwm,
                        pOut,
                        iOut,
                        dOut
                    )
                )

        # Save PWM Outputs
        if GPIO.input(pinBrew):
            # print('Output')
            # with open('/media/pi/SPRATAPI/PID/PWM.txt', 'a+') as file:
            #     file.write(str(targetPwm) + '\n')
            targetPwm = 10
        else:
            pass

        # Set PWM
        outPwm.ChangeDutyCycle(targetPwm)

        # Update previousTemp
        previousTemp = copy.deepcopy(temp)

        # Delay
        time.sleep(sample)

    except KeyboardInterrupt:
        # Terminate PWM
        outPwm.stop()

        # Cleanup GPIO
        GPIO.cleanup()

        print('Program Interrupted')
        os._exit(1)
