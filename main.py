# --------------------------------------------------
# Import Packages
# --------------------------------------------------

import os
import csv
import random
import math
import ast
import tkinter as tk
import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.stats.stats import pearsonr

# --------------------------------------------------
# Assign Global Variables and Import Configuration
# --------------------------------------------------

# Initialize Global Variables
testEnv = True
idling = True
running = False
flashing = False
counter = 0
tempLst = []
presLst = []
configDict = {}
applicationLoc = os.path.dirname(__file__)

# Configure Environment
if testEnv:
    diagDictVar = 'testDiagsLoc'
    dirSep = '\\'
else:
    diagDictVar = 'saveDiagsLoc'
    dirSep = '/'

    # --------------------------------------------------
    # Import Sensor Packages
    # --------------------------------------------------

    import board
    import RPi.GPIO as GPIO
    import busio
    import digitalio
    import adafruit_max31855 as AdaT
    import Adafruit_ADS1x15 as AdaP

    # --------------------------------------------------
    # Initialize Sensors
    # --------------------------------------------------

    spi = busio.SPI(
        board.SCK,
        MOSI=board.MOSI,
        MISO=board.MISO
    )
    cs = digitalio.DigitalInOut(
        board.D5
    )
    Amp = AdaT.MAX31855(
        spi,
        cs
    )
    Adc = AdaP.ADS1115(
        address=0x48,
        busnum=1
    )
    GPIO.setup(
        14,
        GPIO.OUT
    )

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
    print(
        applicationLoc + dirSep +
        'config' + dirSep + 'config.txt'
    )
    exit()

# Assign Extraction ID
if os.path.isdir(configDict[diagDictVar]):
    databaseLst = os.listdir(configDict[diagDictVar])
    databaseLst = [
        item for item in databaseLst
        if ('Diagnostics_' and '.csv') in item
    ]

    # If No Database File Exists, then Create ID
    if databaseLst == []:
        uniqueID = 1

    # If Database Files Exists, then Get Max ID
    else:
        uniqueID = int(
            max(
                [
                    int(Item.split('_')[1])
                    for Item in databaseLst
                ]
            ) + 1
        )
else:
    print('ERROR: Improper Diagnostics Location Provided in config.')
    print(
        '       Please Provide Real Directory Path for ' +
        configDict[diagDictVar] + '.'
    )
    exit()

# --------------------------------------------------
# Define GUI Navigation Functions
# --------------------------------------------------


def button_press():
    print('Click')


def error(
    message
):
    global configDict, testEnv

    # Declare Error Container
    error = tk.Toplevel(
        master=root,
        width=342,
        height=129,
        background=configDict['color4']
    )
    error.title('Error')

    # Assign Environment Settings
    if not testEnv:
        error.configure(cursor='none')

    for c in range(0, 3):
        error.columnconfigure(
            c,
            minsize=114,
            weight=1
        )

    for r in range(0, 3):
        error.rowconfigure(
            r,
            minsize=43,
            weight=1
        )

    # Position Error Frame
    error.geometry(
        '+{}+{}'.format(
            int(error.winfo_screenwidth() / 2
                - error.winfo_reqwidth() / 2),
            int(error.winfo_screenheight() / 3
                - error.winfo_reqheight() / 2)
        )
    )

    # Declare Error Components
    labelError = tk.Label(
        error,
        text='Error: ' + message,
        font=(
            configDict['font'],
            configDict['labelSize']
        ),
        bg=configDict['color4'],
        fg=configDict['color1']
    )
    buttonOkay = tk.Button(
        error,
        height=configDict['buttonH'],
        width=configDict['buttonW'],
        text='Okay',
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['color3'],
        fg=configDict['color1'],
        command=lambda: back(error)
    )

    # Pack Error Components
    labelError.grid(
        column=0,
        row=0,
        columnspan=3,
        rowspan=2,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonOkay.grid(
        column=2,
        row=2,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )


def close():
    global idling, running, flashing

    idling = False
    running = False
    flashing = False

    # Close the Top Frame
    root.destroy()
    exit()


def back(
    frame
):

    # Close the Top Frame
    frame.destroy()


def save_extraction(
    labelCounter,
    buttonStart,
    buttonStop,
    buttonReset,
    buttonPlot,
    buttonSave,
    buttonSettings,
    buttonBack
):
    global idling, running, flashing, counter, tempLst, presLst, uniqueID
    global configDict, tkCounter, tkTempValue, tkPresValue

    # Clear Dataframe
    extractionDS = pd.DataFrame()

    # Create Time Series List
    timeLst = [
        round(item / 10, 1)
        for item in list(
            range(
                0,
                len(tempLst)
            )
        )
    ]

    # Import Pressure Profile
    profDict = {}

    if os.path.isfile(
        applicationLoc + dirSep +
        'config' + dirSep + 'profiles' + dirSep +
        configDict['profile'] + '.txt'
    ):
        with open(
            applicationLoc + dirSep
            + 'config' + dirSep + 'profiles' + dirSep
            + configDict['profile'] + '.txt'
        ) as file:
            for line in file:
                (var, val) = line.split('|')
                try:
                    profDict[var] = int(val)
                except ValueError:
                    profDict[var] = str(val).strip('\n')

    # Generate Descrptive Series Lists
    username = [configDict['username']] * len(tempLst)
    uniqueIDLst = [uniqueID] * len(tempLst)
    date = [dt.datetime.now().strftime('%d/%b/%Y').upper()] * len(tempLst)
    time = [dt.datetime.now().strftime('%H:%M:%S')] * len(tempLst)
    tUnit = [configDict['scale'].split(' ')[1][1]] * len(tempLst)
    pUnit = ['Bars'] * len(tempLst)
    maxDuration = [max(timeLst)] * len(tempLst)
    minTemp = [min(tempLst)] * len(tempLst)
    maxTemp = [max(tempLst)] * len(tempLst)
    minPressure = [min(presLst)] * len(tempLst)
    maxPressure = [max(presLst)] * len(tempLst)
    tempSetPoint = [configDict['setPoint']] * len(tempLst)

    if configDict['profile'].upper() == 'MANUAL':
        profile = [configDict['profile']] * len(tempLst)
        presProf = [0] * len(tempLst)
    else:
        profile = [configDict['profile']] * len(tempLst)
        presProf = ast.literal_eval(profDict['profLst'])

    # Built Dataframe from Times, Temperatures and Pressures
    extractionDS = pd.DataFrame(
        data={
            'User': username,
            'UniqueID': uniqueIDLst,
            'Date': date,
            'Time': time,
            'Duration': timeLst,
            'Temperature': tempLst,
            'TUnit': tUnit,
            'Pressure': presLst,
            'PUnit': pUnit,
            'MaxDuration': maxDuration,
            'MinTemp': minTemp,
            'MaxTemp': maxTemp,
            'MinPressure': minPressure,
            'MaxPressure': maxPressure,
            'TempSetPoint': tempSetPoint,
            'Profile': profile,
            'ProfileValues': presProf
        },
        columns=[
            'User',
            'UniqueID',
            'Date',
            'Time',
            'Duration',
            'Temperature',
            'TUnit',
            'Pressure',
            'PUnit',
            'MaxDuration',
            'MinTemp',
            'MaxTemp',
            'MinPressure',
            'MaxPressure',
            'TempSetPoint',
            'Profile',
            'ProfileValues'
        ]
    )

    # Export Diagnostics Dataframe
    extractionDS.to_csv(
        path_or_buf=(
            configDict[diagDictVar] + dirSep + 'Diagnostics_'
            + str(uniqueID)
            + '_'
            + date[0].replace('/', '')
            + '.csv'
        ),
        sep=',',
        index=False
    )

    # Configure Operation State
    idling = True
    running = False
    flashing = False
    counter = 0
    tempLst = []
    presLst = []

    # Update Components
    tkCounter.set(float(round(counter / 10, 1)))
    tkTempValue.set(read_temp())
    tkPresValue.set(read_pressure())

    labelCounter.configure(fg=configDict['color1'])
    buttonStart.configure(state=tk.NORMAL)
    buttonStop.configure(state=tk.DISABLED)
    buttonReset.configure(state=tk.DISABLED)
    buttonPlot.configure(state=tk.DISABLED)
    buttonSave.configure(state=tk.DISABLED)
    buttonSettings.configure(state=tk.NORMAL)
    buttonBack.configure(state=tk.NORMAL)

    # Trigger Start of Idle Temperature
    idle()


def save_settings(
    frame
):
    global configDict

    # Write Out config Changes
    with open(
        applicationLoc + dirSep +
        'config' + dirSep + 'config.txt',
        mode='w',
        newline=''
    ) as file:
        configWriter = csv.writer(
            file,
            delimiter='|'
        )

        for var, val in configDict.items():
            configWriter.writerow([var, val])

    # Close the Top Frame
    frame.destroy()


def check_profile(
    frame,
    customDict,
    tkProfileName
):
    global configDict, testEnv

    # Update Profile Name Value
    customDict['profileName'] = tkProfileName.get()

    # Check if Profile Name Already Exists
    if os.path.isdir(
        applicationLoc + dirSep +
        'config' + dirSep + 'profiles'
    ):
        profileLst = [
            item.split('.')[0]
            for item in os.listdir(
                applicationLoc + dirSep
                + 'config' + dirSep + 'profiles'
            )
        ]

    if customDict['profileName'] in profileLst:
        # Declare Warning Container
        warning = tk.Toplevel(
            master=root,
            width=342,
            height=129,
            background=configDict['color4']
        )
        warning.title('Warning')

        # Assign Environment Settings
        if not testEnv:
            warning.configure(cursor='none')

        for c in range(0, 3):
            warning.columnconfigure(
                c,
                minsize=114,
                weight=1
            )
        for r in range(0, 3):
            warning.rowconfigure(
                r,
                minsize=43,
                weight=1
            )

        # Position Warning Frame
        warning.geometry(
            '+{}+{}'.format(
                int(warning.winfo_screenwidth() / 2
                    - warning.winfo_reqwidth() / 2),
                int(warning.winfo_screenheight() / 3
                    - warning.winfo_reqheight() / 2)
            )
        )

        # Define Warning Message
        message0 = '['+customDict['profileName'] + '] already exists.'
        message1 = 'Do you want to overwrite it?'

        # Declare Warning Components
        labelWarning0 = tk.Label(
            warning,
            text=message0,
            font=(
                configDict['font'],
                configDict['labelSize']
            ),
            bg=configDict['color4'],
            fg=configDict['color1']
        )
        labelWarning1 = tk.Label(
            warning,
            text=message1,
            font=(
                configDict['font'],
                configDict['labelSize']
            ),
            bg=configDict['color4'],
            fg=configDict['color1']
        )
        buttonNo = tk.Button(
            warning,
            height=configDict['buttonH'],
            width=configDict['buttonW'],
            text='No',
            font=(
                configDict['font'],
                configDict['buttonSize']
            ),
            bg=configDict['color3'],
            fg=configDict['color1'],
            command=lambda: back(warning)
        )
        buttonYes = tk.Button(
            warning,
            height=configDict['buttonH'],
            width=configDict['buttonW'],
            text='Yes',
            font=(
                configDict['font'],
                configDict['buttonSize']
            ),
            bg=configDict['color3'],
            fg=configDict['color1'],
            command=lambda: save_profile(
                frame,
                customDict,
                True,
                warning
            )
        )

        # Pack Warning Components
        labelWarning0.grid(
            column=0,
            row=0,
            columnspan=3,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.W
        )
        labelWarning1.grid(
            column=0,
            row=1,
            columnspan=3,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        buttonNo.grid(
            column=0,
            row=2,
            columnspan=1,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        buttonYes.grid(
            column=2,
            row=2,
            columnspan=1,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )

    else:
        # Set Dummy Warning Frame
        warning = ''

        # Write out Profile
        save_profile(
            frame,
            customDict,
            False,
            warning
        )


def delete_profile(
    selectProfile
):
    global configDict, testEnv

    def delete(frame, selectProfile):
        global configDict, testEnv

        # Delete Selected Profile
        if os.path.isfile(
            applicationLoc + dirSep +
            'config' + dirSep + 'profiles' + dirSep +
            configDict['profile'] + '.txt'
        ):
            os.remove(
                applicationLoc + dirSep +
                'config' + dirSep + 'profiles' + dirSep +
                configDict['profile'] + '.txt'
            )

        # Reset Profile Variable to Manual
        configDict['profile'] = 'Manual'
        tkProfile.set(configDict['profile'])

        # Refresh Profile Dropdown
        refresh_settings(selectProfile)

        # Close Confirmation Frame
        frame.destroy()

    # Check if Manual Profile is Selected
    if configDict['profile'].upper() == 'MANUAL':
        error(
            '[Manual] profile cannot be deleted.'
        )
    else:
        # Check if Profile Name Already Exists
        if os.path.isdir(
            applicationLoc + dirSep +
            'config' + dirSep + 'profiles'
        ):
            profileLst = [
                item.split('.')[0]
                for item in os.listdir(
                    applicationLoc + dirSep +
                    'config' + dirSep + 'profiles'
                )
            ]

        if configDict['profile'] in profileLst:
            # Declare Confirm Container
            confirm = tk.Toplevel(
                master=root,
                width=342,
                height=129,
                background=configDict['color4']
            )
            confirm.title('Confirm')

            # Assign Environment Settings
            if not testEnv:
                confirm.configure(cursor='none')

            for c in range(0, 3):
                confirm.columnconfigure(
                    c,
                    minsize=114,
                    weight=1
                )
            for r in range(0, 3):
                confirm.rowconfigure(
                    r,
                    minsize=43,
                    weight=1
                )

            # Position Confirm Frame
            confirm.geometry(
                '+{}+{}'.format(
                    int(confirm.winfo_screenwidth() / 2
                        - confirm.winfo_reqwidth() / 2),
                    int(confirm.winfo_screenheight() / 3
                        - confirm.winfo_reqheight() / 2)
                )
            )

            # Define Confirm Message
            message = (
                'Are you sure you want to delete [' +
                configDict['profile'] + ']?'
            )

            # Declare Confirm Components
            labelConfirm = tk.Label(
                confirm,
                text=message,
                font=(
                    configDict['font'],
                    configDict['labelSize']
                ),
                bg=configDict['color4'],
                fg=configDict['color1']
            )
            buttonNo = tk.Button(
                confirm,
                height=configDict['buttonH'],
                width=configDict['buttonW'],
                text='No',
                font=(
                    configDict['font'],
                    configDict['buttonSize']
                ),
                bg=configDict['color3'],
                fg=configDict['color1'],
                command=lambda: back(confirm)
            )
            buttonYes = tk.Button(
                confirm,
                height=configDict['buttonH'],
                width=configDict['buttonW'],
                text='Yes',
                font=(
                    configDict['font'],
                    configDict['buttonSize']
                ),
                bg=configDict['color3'],
                fg=configDict['color1'],
                command=lambda: delete(
                    confirm,
                    selectProfile
                )
            )

            # Pack Warning Components
            labelConfirm.grid(
                column=0,
                row=0,
                columnspan=3,
                rowspan=2,
                padx=configDict['padX'],
                pady=configDict['padY'],
                sticky=tk.N+tk.S+tk.E+tk.W
            )
            buttonNo.grid(
                column=0,
                row=2,
                columnspan=1,
                rowspan=1,
                padx=configDict['padX'],
                pady=configDict['padY'],
                sticky=tk.N+tk.S+tk.E+tk.W
            )
            buttonYes.grid(
                column=2,
                row=2,
                columnspan=1,
                rowspan=1,
                padx=configDict['padX'],
                pady=configDict['padY'],
                sticky=tk.N+tk.S+tk.E+tk.W
            )


def save_profile(
    frame,
    customDict,
    inputWarning,
    warningFrame
):
    global configDict

    # Close Warning Frame
    if inputWarning:
        warningFrame.destroy()

    # Write Out Profile
    if os.path.isdir(
        applicationLoc + dirSep +
        'config' + dirSep + 'profiles'
    ):
        with open(
            applicationLoc + dirSep +
            'config' + dirSep + 'profiles' +
            dirSep + customDict['profileName'] + '.txt',
            mode='w',
            newline=''
        ) as file:
            profileWriter = csv.writer(
                file,
                delimiter='|'
            )

            for var, val in customDict.items():
                profileWriter.writerow([var, val])

        # Close the Top Frame
        frame.destroy()


def refresh_settings(selectProfile):
    global configDict, tkProfile

    # Refresh List of Pressure Profiles
    if os.path.isdir(
        applicationLoc + dirSep +
        'config' + dirSep + 'profiles'
    ):
        profileLst = sorted(
            [
                item.split('.')[0]
                for item in os.listdir(
                    applicationLoc + dirSep +
                    'config' + dirSep + 'profiles'
                )
            ]
        )

    # Update the OptionMenu
    selectProfile['menu'].delete(0, 'end')
    for option in profileLst:
        selectProfile['menu'].add_command(
            label=option,
            command=tk._setit(
                tkProfile,
                option,
                profile_callback
            )
        )

# --------------------------------------------------
# Define Operation Functions
# --------------------------------------------------


def read_temp():
    global configDict, testEnv

    if testEnv:
        return random.randint(195, 205)
    else:
        try:
            temp = round(Amp.temperature, 2)
        except RuntimeError:
            pass

        if configDict['scale'].split(' ')[1] == '[F]':
            return int(temp * 9 / 5 + 32)
        else:
            return int(temp)


def read_pressure():
    global testEnv

    if testEnv:
        return float(random.randint(30, 90) / 10)
    else:
        try:
            pres = round(
                (3.0 / 1750) *
                (Adc.read_adc(
                    0,
                    gain=2 / 3
                )) - (34.0 / 7.0), 1
            )
        except RuntimeError:
            pass

        return pres


def idle():
    global idling
    global configDict, tkTempValue, tkPresValue

    if idling:
        # Read Sensor Values
        tkTempValue.set(read_temp())
        tkPresValue.set(read_pressure())

        # Recursive Idle
        root.after(100, idle)


def start(
    labelCounter,
    buttonStart,
    buttonStop,
    buttonReset,
    buttonPlot,
    buttonSave,
    buttonSettings,
    buttonBack
):
    global idling, running, flashing, counter, tempLst, presLst
    global configDict, tkCounter, tkTempValue, tkPresValue

    # Configure Operation State
    idling = False
    running = True
    flashing = False

    if not testEnv:
        print('Start')
        GPIO.output(14, GPIO.HIGH)

    # Update Components
    labelCounter.configure(fg=configDict['color1'])
    buttonStart.configure(state=tk.DISABLED)
    buttonStop.configure(state=tk.NORMAL)
    buttonReset.configure(state=tk.NORMAL)
    buttonPlot.configure(state=tk.DISABLED)
    buttonSave.configure(state=tk.DISABLED)
    buttonSettings.configure(state=tk.DISABLED)
    buttonBack.configure(state=tk.DISABLED)

    def count(
        countStart,
        profDict,
        manual
    ):
        global running, counter, tempLst, presLst
        global tkCounter, tkTempValue, tkPresValue

        if running:
            # Append Sensor Values
            tempLst.append(read_temp())
            presLst.append(read_pressure())

            # Update Label Text
            tkCounter.set(float(round(counter / 10, 1)))
            tkTempValue.set(tempLst[counter])
            tkPresValue.set(presLst[counter])

            # Increment Counter
            counter += 1

            # Delay
            if manual:
                root.after(
                    int(
                        100 - (
                            (
                                dt.datetime.now() - countStart
                            ).total_seconds() * 1000
                        )
                    ),
                    lambda: count(
                        dt.datetime.now(),
                        profDict,
                        True
                    )
                )
            else:
                if (
                    round(counter / 10, 1) >
                    max(ast.literal_eval(profDict['timeLst']))
                ):
                    stop(
                        labelCounter,
                        buttonStart,
                        buttonStop,
                        buttonReset,
                        buttonPlot,
                        buttonSave,
                        buttonSettings,
                        buttonBack
                    )
                else:
                    root.after(
                        int(
                            100 - (
                                (
                                    dt.datetime.now() - countStart
                                ).total_seconds() * 1000
                            )
                        ),
                        lambda: count(
                            dt.datetime.now(),
                            profDict,
                            False
                        )
                    )

    # Retrieve Pressure Profile Settings
    profDict = {}

    if os.path.isfile(
        applicationLoc + dirSep +
        'config' + dirSep + 'profiles'
        + dirSep + configDict['profile'] + '.txt'
    ):
        with open(
            applicationLoc + dirSep +
            'config' + dirSep + 'profiles' +
            dirSep + configDict['profile'] + '.txt'
        ) as file:
            for line in file:
                (var, val) = line.split('|')
                try:
                    profDict[var] = int(val)
                except ValueError:
                    profDict[var] = str(val).strip('\n')

    if configDict['profile'].upper() == 'MANUAL':

        # Allow Manual Control of Timer
        count(
            dt.datetime.now(),
            profDict,
            True
        )
    else:
        # Disable Stop Button
        buttonStop.configure(state=tk.DISABLED)

        # Enforce Program Control of Timer
        count(
            dt.datetime.now(),
            profDict,
            False
        )


def stop(
    labelCounter,
    buttonStart,
    buttonStop,
    buttonReset,
    buttonPlot,
    buttonSave,
    buttonSettings,
    buttonBack
):
    global idling, running, flashing
    global configDict

    # Configure Operation State
    idling = False
    running = False
    flashing = True

    if not testEnv:
        print('Stop')
        GPIO.output(14, GPIO.LOW)

    # Update Components
    buttonStart.configure(state=tk.NORMAL)
    buttonStop.configure(state=tk.DISABLED)
    buttonReset.configure(state=tk.NORMAL)
    buttonPlot.configure(state=tk.NORMAL)
    buttonSave.configure(state=tk.NORMAL)
    buttonSettings.configure(state=tk.DISABLED)
    buttonBack.configure(state=tk.DISABLED)

    def flash(
        labelCounter,
        countStart
    ):
        global configDict

        if flashing:
            # Retrive Background and Foreground
            tkinterBG = labelCounter.cget('background')
            labelFG = labelCounter.cget('foreground')

            if labelFG == tkinterBG:
                labelCounter.configure(
                    fg=configDict['color1']
                )
            else:
                labelCounter.configure(
                    fg=tkinterBG
                )

            # Delay
            root.after(
                int(
                    500 - (
                        (
                            dt.datetime.now() - countStart
                        ).total_seconds() * 1000
                    )
                ),
                lambda: flash(
                    labelCounter,
                    dt.datetime.now()
                )
            )

    # Trigger Start of Flashing
    flash(
        labelCounter,
        dt.datetime.now()
    )


def reset(
    labelCounter,
    buttonStart,
    buttonStop,
    buttonReset,
    buttonPlot,
    buttonSave,
    buttonSettings,
    buttonBack
):
    global idling, running, flashing, counter, tempLst, presLst
    global configDict, tkCounter, tkTempValue, tkPresValue

    # Configure Operation State
    idling = True
    running = False
    flashing = False
    counter = 0
    tempLst = []
    presLst = []

    # Update Components
    tkCounter.set(float(round(counter / 10, 1)))
    tkTempValue.set(read_temp())
    tkPresValue.set(read_pressure())

    labelCounter.configure(fg=configDict['color1'])
    buttonStart.configure(state=tk.NORMAL)
    buttonStop.configure(state=tk.DISABLED)
    buttonReset.configure(state=tk.DISABLED)
    buttonPlot.configure(state=tk.DISABLED)
    buttonSave.configure(state=tk.DISABLED)
    buttonSettings.configure(state=tk.NORMAL)
    buttonBack.configure(state=tk.NORMAL)

    # Trigger Start of Idle Temperature
    idle()

# --------------------------------------------------
# Define Variable callback Functions
# --------------------------------------------------


def scale_callback(
    value,
    selectSetPoint,
    setPointLst
):
    global configDict, tkSetPoint

    # Assign Temperature Range Based on Scale Value
    if configDict['scale'].split(' ')[1] != value.split(' ')[1]:
        if value.split(' ')[1] == '[F]':

            # Convert from Celsius to Fahrenheit
            setPointLst = list(np.arange(215, 236, 1))
            configDict['setPoint'] = int(
                (
                    tkSetPoint.get() * 9 / 5
                ) + 32
            )

            # Limit Upper and Lower Bounds
            if configDict['setPoint'] < 215:
                configDict['setPoint'] = 215
            elif configDict['setPoint'] > 236:
                configDict['setPoint'] = 236
            else:
                pass

        else:
            # Convert from Fahrenheit to Celsius
            setPointLst = [
                round(item, 1)
                for item in list(
                    np.arange(
                        100,
                        114.5,
                        0.5
                    )
                )
            ]
            configDict['setPoint'] = float(
                round(
                    (
                        (
                            tkSetPoint.get() - 32
                        ) * 5 / 9
                    ) * 2
                ) / 2
            )

            # Limit Upper and Lower Bounds
            if configDict['setPoint'] < 100:
                configDict['setPoint'] = 100
            elif configDict['setPoint'] > 114.5:
                configDict['setPoint'] = 114.5
            else:
                pass

    else:
        pass

    configDict['scale'] = value
    tkSetPoint.set(configDict['setPoint'])

    # Update the OptionMenu
    selectSetPoint['menu'].delete(0, 'end')
    for option in setPointLst:
        selectSetPoint['menu'].add_command(
            label=option,
            command=tk._setit(
                tkSetPoint,
                option,
                setpoint_callback
            )
        )


def setpoint_callback(
    value
):
    global configDict
    configDict['setPoint'] = value


def profile_callback(
    value
):
    global configDict
    configDict['profile'] = value


def flush_callback(
    value
):
    global configDict
    configDict['flush'] = value

# --------------------------------------------------
# Build Dashboard Frame
# --------------------------------------------------


def create_dashboard():
    global configDict, testEnv

    # Declare Dashboard Container
    dashboard = tk.Toplevel(
        master=root,
        width=800,
        height=480,
        background=configDict['color4']
    )
    dashboard.title('Dashboard')

    # Assign Environment Settings
    if not testEnv:
        dashboard.attributes('-fullscreen', True)
        dashboard.configure(cursor='none')

    for c in range(0, 7):
        dashboard.columnconfigure(
            c,
            minsize=114,
            weight=1
        )

    for r in range(0, 11):
        dashboard.rowconfigure(
            r,
            minsize=43,
            weight=1
        )

    # Declare Dashboard Components
    buttonBack = tk.Button(
        dashboard,
        height=configDict['buttonH'],
        width=configDict['buttonW'],
        text='Back',
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['color3'],
        fg=configDict['color1'],
        command=lambda: back(dashboard)
    )
    buttonClose = tk.Button(
        dashboard,
        height=configDict['buttonH'],
        width=configDict['buttonW'],
        text='Close',
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['color3'],
        fg=configDict['color1'],
        command=close
    )
    buttonFlush = tk.Button(
        dashboard,
        height=configDict['buttonH'],
        width=configDict['buttonW'],
        text='Flush',
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['color3'],
        fg=configDict['color1'],
        command=button_press,
        state=tk.DISABLED
    )
    buttonStart = tk.Button(
        dashboard,
        height=configDict['buttonH'] * 2,
        width=configDict['buttonW'],
        text='Start',
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['green'],
        fg=configDict['color1'],
        command=lambda: start(
            labelCounter,
            buttonStart,
            buttonStop,
            buttonReset,
            buttonPlot,
            buttonSave,
            buttonSettings,
            buttonBack
        )
    )
    buttonStop = tk.Button(
        dashboard,
        height=configDict['buttonH'] * 2,
        width=configDict['buttonW'],
        text='Stop',
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['red'],
        fg=configDict['color1'],
        state='disabled',
        command=lambda: stop(
            labelCounter,
            buttonStart,
            buttonStop,
            buttonReset,
            buttonPlot,
            buttonSave,
            buttonSettings,
            buttonBack
        )
    )
    buttonSave = tk.Button(
        dashboard,
        height=configDict['buttonH'],
        width=configDict['buttonW'],
        text='Save',
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['color3'],
        fg=configDict['color1'],
        state='disabled',
        command=lambda: save_extraction(
            labelCounter,
            buttonStart,
            buttonStop,
            buttonReset,
            buttonPlot,
            buttonSave,
            buttonSettings,
            buttonBack
        )
    )
    buttonReset = tk.Button(
        dashboard,
        height=configDict['buttonH'],
        width=configDict['buttonW'],
        text='Reset',
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['color3'],
        fg=configDict['color1'],
        state='disabled',
        command=lambda: reset(
            labelCounter,
            buttonStart,
            buttonStop,
            buttonReset,
            buttonPlot,
            buttonSave,
            buttonSettings,
            buttonBack
        )
    )
    buttonPlot = tk.Button(
        dashboard,
        height=configDict['buttonH'] * 2,
        width=configDict['buttonW'],
        text='Plot',
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['color3'],
        fg=configDict['color1'],
        state='disabled',
        command=lambda: create_plot()
    )
    buttonSettings = tk.Button(
        dashboard,
        height=configDict['buttonH'] * 2,
        width=configDict['buttonW'],
        text='Settings',
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['color3'],
        fg=configDict['color1'],
        command=create_settings
    )
    labelCounter = tk.Label(
        dashboard,
        textvariable=tkCounter,
        font=(
            configDict['font'],
            configDict['counterSize'],
            'bold'
        ),
        bg=configDict['color4'],
        fg=configDict['color1']
    )
    labelTDesc = tk.Label(
        dashboard,
        textvariable=tkScale,
        font=(
            configDict['font'],
            configDict['headerSize']
        ),
        bg=configDict['color4'],
        fg=configDict['color1']
    )
    valueTMetric = tk.Label(
        dashboard,
        textvariable=tkTempValue,
        font=(
            configDict['font'],
            configDict['metricsSize'],
            'bold'
        ),
        bg=configDict['color4'],
        fg=configDict['blue']
    )
    labelPDesc = tk.Label(
        dashboard,
        text='Pressure [Bars]',
        font=(
            configDict['font'],
            configDict['headerSize']
        ),
        bg=configDict['color4'],
        fg=configDict['color1']
    )
    valuePMetric = tk.Label(
        dashboard,
        textvariable=tkPresValue,
        font=(
            configDict['font'],
            configDict['metricsSize'],
            'bold'
        ),
        bg=configDict['color4'],
        fg=configDict['red']
    )
    labelSet = tk.Label(
        dashboard,
        text='Set-Point:',
        font=(
            configDict['font'],
            configDict['labelSize']
        ),
        bg=configDict['color4'],
        fg=configDict['color1']
    )
    valueSet = tk.Label(
        dashboard,
        textvariable=tkSetPoint,
        font=(
            configDict['font'],
            configDict['labelSize'],
            'bold'
        ),
        bg=configDict['color4'],
        fg=configDict['blue']
    )
    labelFlush = tk.Label(
        dashboard,
        text='Flush [Sec.]:',
        font=(
            configDict['font'],
            configDict['labelSize']
        ),
        bg=configDict['color4'],
        fg=configDict['color1']
    )
    valueFlush = tk.Label(
        dashboard,
        textvariable=tkFlush,
        font=(
            configDict['font'],
            configDict['labelSize'],
            'bold'
        ),
        bg=configDict['color4'],
        fg=configDict['color1']
    )
    labelProfile = tk.Label(
        dashboard,
        text='Profile:',
        font=(
            configDict['font'],
            configDict['labelSize']
        ),
        bg=configDict['color4'],
        fg=configDict['color1']
    )
    valueProfile = tk.Label(
        dashboard,
        textvariable=tkProfile,
        font=(
            configDict['font'],
            configDict['labelSize'],
            'bold'
        ),
        bg=configDict['color4'],
        fg=configDict['color1']
    )

    # Pack Dashboard Components
    buttonBack.grid(
        column=0,
        row=0,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonClose.grid(
        column=6,
        row=0,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonFlush.grid(
        column=0,
        row=1,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonStart.grid(
        column=1,
        row=8,
        columnspan=1,
        rowspan=2,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonStop.grid(
        column=2,
        row=8,
        columnspan=1,
        rowspan=2,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonSave.grid(
        column=3,
        row=8,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonReset.grid(
        column=3,
        row=9,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonPlot.grid(
        column=4,
        row=8,
        columnspan=1,
        rowspan=2,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonSettings.grid(
        column=5,
        row=8,
        columnspan=1,
        rowspan=2,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    labelCounter.grid(
        column=0,
        row=2,
        columnspan=4,
        rowspan=5,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    labelTDesc.grid(
        column=3,
        row=2,
        columnspan=2,
        rowspan=2,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    valueTMetric.grid(
        column=5,
        row=2,
        columnspan=2,
        rowspan=2,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    labelPDesc.grid(
        column=3,
        row=5,
        columnspan=2,
        rowspan=2,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    valuePMetric.grid(
        column=5,
        row=5,
        columnspan=2,
        rowspan=2,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    labelSet.grid(
        column=0,
        row=10,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    valueSet.grid(
        column=1,
        row=10,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    labelFlush.grid(
        column=2,
        row=10,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    valueFlush.grid(
        column=3,
        row=10,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    labelProfile.grid(
        column=4,
        row=10,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    valueProfile.grid(
        column=5,
        row=10,
        columnspan=2,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.W
    )

# --------------------------------------------------
# Build Plot Frame
# --------------------------------------------------


def create_plot():
    global configDict, tempLst, presLst, testEnv

    # Declare Plot Container
    plot = tk.Toplevel(
        master=root,
        width=800,
        height=480,
        background=configDict['color4']
    )
    plot.title('Extraction database')

    # Assign Environment Settings
    if not testEnv:
        plot.attributes('-fullscreen', True)
        plot.configure(cursor='none')

    for c in range(0, 7):
        plot.columnconfigure(
            c,
            minsize=114,
            weight=1
        )

    for r in range(0, 11):
        plot.rowconfigure(
            r,
            minsize=43,
            weight=1
        )

    # Define Callback to Generate a Pressure Profile from Manual Extraction
    def add_profile(
        timeLst,
        profLst
    ):
        global configDict, testEnv

        # Create Pressure Profile Dictionary
        if os.path.isdir(
            applicationLoc + dirSep +
            'config' + dirSep + 'profiles'
        ):
            profileLst = [
                item.split('.')[0]
                for item in os.listdir(
                    applicationLoc + dirSep +
                    'config' + dirSep + 'profiles'
                )
            ]
            userProfiles = [
                item for item in profileLst
                if 'USER_' in item.upper()
            ]
            if userProfiles == []:
                profileNum = 1
            else:
                profileNum = int(
                    max(
                        int(
                            item.split('_')[1]
                        )
                        for item in userProfiles
                    ) + 1
                )

        userDict = {
            'profileName': 'User_'+str(profileNum),
            'extractionDuration': float(round(max(timeLst), 1)),
            'infusionDuration': 0,
            'infusionPressure': 3,
            'p0': 9,
            'p1': 9,
            'p2': 9,
            'p3': 9,
            'p4': 9,
            'timeLst': timeLst,
            'profLst': profLst
        }

        # Create User Input ProfileName
        profileName = tk.Toplevel(
            master=root,
            width=342,
            height=129,
            background=configDict['color4']
        )
        profileName.title('Input Profile Name')

        # Assign Environment Settings
        if not testEnv:
            profileName.configure(cursor='none')

        for c in range(0, 3):
            profileName.columnconfigure(
                c,
                minsize=114,
                weight=1
            )

        for r in range(0, 3):
            profileName.rowconfigure(
                r,
                minsize=43,
                weight=1
            )

        # Position Profile Name Frame
        profileName.geometry(
            '+{}+{}'.format(
                int(profileName.winfo_screenwidth() / 2
                    - profileName.winfo_reqwidth() / 2),
                int(profileName.winfo_screenheight() / 3
                    - profileName.winfo_reqheight() / 2)
            )
        )

        tkUserProfileName = tk.StringVar()
        tkUserProfileName.set('User_'+str(profileNum))

        # Declare Profile Name Components
        labelProfileName = tk.Label(
            profileName,
            text='Profile Name:',
            font=(
                configDict['font'],
                configDict['buttonSize']
            ),
            bg=configDict['color4'],
            fg=configDict['color1']
        )
        valueProfileName = tk.Entry(
            profileName,
            textvariable=tkUserProfileName,
            font=(
                configDict['font'],
                configDict['labelSize'],
                'bold'
            ),
            bg=configDict['color3'],
            fg=configDict['color1']
        )
        buttonBack = tk.Button(
            profileName,
            height=configDict['buttonH'],
            width=configDict['buttonW'],
            text='Back',
            font=(
                configDict['font'],
                configDict['buttonSize']
            ),
            bg=configDict['color3'],
            fg=configDict['color1'],
            command=lambda: back(profileName)
        )
        buttonAddProfile = tk.Button(
            profileName,
            height=configDict['buttonH'],
            width=configDict['buttonW'],
            text='Okay',
            font=(
                configDict['font'],
                configDict['buttonSize']
            ),
            bg=configDict['color3'],
            fg=configDict['color1'],
            command=lambda: check_profile(
                profileName,
                userDict,
                tkUserProfileName
            )
        )

        # Pack Profile Name Components
        labelProfileName.grid(
            column=0,
            row=0,
            columnspan=1,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.W
        )
        valueProfileName.grid(
            column=0,
            row=1,
            columnspan=3,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        buttonBack.grid(
            column=1,
            row=2,
            columnspan=1,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        buttonAddProfile.grid(
            column=2,
            row=2,
            columnspan=1,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )

    # Create Time Series List
    timeLst = [
        round(item / 10, 1)
        for item in list(
            range(
                0,
                len(tempLst)
            )
        )
    ]

    # Import Pressure Profile
    profDict = {}

    if os.path.isfile(
        applicationLoc + dirSep +
        'config' + dirSep + 'profiles' +
        dirSep + configDict['profile'] + '.txt'
    ):
        with open(
            applicationLoc + dirSep +
            'config' + dirSep + 'profiles' +
            dirSep + configDict['profile'] + '.txt'
        ) as file:
            for line in file:
                (var, val) = line.split('|')
                try:
                    profDict[var] = int(val)
                except ValueError:
                    profDict[var] = str(val).strip('\n')

    if configDict['profile'].upper() == 'MANUAL':
        correl = 'NA'
        plotProfile = False
    else:
        if os.path.isfile(
            applicationLoc + dirSep +
            'config' + dirSep + 'profiles'
            + dirSep + configDict['profile'] + '.txt'
        ):
            # Calculate Statistics
            correl = float(
                round(
                    pearsonr(
                        presLst,
                        ast.literal_eval(
                            profDict['profLst']
                        )
                    )[0] * 100, 2
                )
            )
            plotProfile = True
        else:
            correl = 'NA'
            plotProfile = False

    # Create Figure for Plot
    fig = plt.figure()
    fig.patch.set_facecolor(configDict['color4'])

    x1 = fig.add_subplot(1, 1, 1)
    x1.set_facecolor(configDict['color3'])
    x2 = x1.twinx()

    for axes in [x1, x2]:
        for border in [
            'top', 'bottom', 'right', 'left'
        ]:
            axes.spines[border].set_color(configDict['color2'])

    # Get DPI and Assign Dimmensions to Figure
    DPI = float(fig.get_dpi())
    fig.set_size_inches(700 / DPI, 350 / DPI)

    # Clear, Format and Plot Temperature Values
    x1.clear()
    x1.set_ylabel(
        'Temperature ' + configDict['scale'].split(' ')[1],
        color=configDict['blue']
    )
    x1.set_xlim(
        min(timeLst),
        max(timeLst)
    )
    x1.set_ylim(
        int(5 * round((min(tempLst)-15) / 5)),
        int(5 * round((max(tempLst)+15) / 5))
    )
    x1.tick_params(
        axis='y',
        labelcolor=configDict['blue'],
        labelsize=configDict['labelSize'] * 0.9,
        length=0,
        pad=10
    )
    x1.tick_params(
        axis='x',
        labelcolor=configDict['color1'],
        labelsize=configDict['labelSize'] * 0.9,
        length=0,
        pad=10
    )
    x1.grid(
        b=True,
        which='both',
        axis='x',
        color=configDict['color2'],
        linestyle='--',
        linewidth=1,
        alpha=0.5
    )
    x1.plot(
        timeLst,
        tempLst,
        linewidth=2,
        color=configDict['blue']
    )
    x1.plot(
        timeLst,
        [configDict['setPoint']] * len(timeLst),
        linewidth=2,
        color=configDict['blue'],
        linestyle='--',
        alpha=0.4
    )
    x1.fill_between(
        timeLst,
        tempLst,
        0,
        linewidth=0,
        color=configDict['blue'],
        alpha=0.4
    )

    # Clear, Format and Plot Pressure Values
    x2.clear()
    x2.set_xlim(
        min(timeLst),
        max(timeLst)
    )
    x2.set_ylim(
        0,
        12
    )
    x2.set_ylabel(
        'Pressure [Bars]',
        color=configDict['red']
    )
    x2.tick_params(
        axis='y',
        labelcolor=configDict['red'],
        labelsize=configDict['labelSize'] * 0.9,
        length=0,
        pad=10
    )
    x2.tick_params(
        axis='x',
        labelcolor=configDict['color1'],
        labelsize=configDict['labelSize'] * 0.9,
        length=0,
        pad=10
    )
    x2.plot(
        timeLst,
        presLst,
        linewidth=2,
        color=configDict['red']
    )

    if plotProfile:
        x2.plot(
            timeLst,
            ast.literal_eval(profDict['profLst']),
            linewidth=2,
            color=configDict['red'],
            linestyle='--',
            alpha=0.4
        )

    if max(timeLst) >= 40:
        x2.set_xticks(
            ticks=np.arange(
                min(timeLst),
                math.ceil(max(timeLst)) + 1,
                2
            )
        )
    else:
        x2.set_xticks(
            ticks=np.arange(
                min(timeLst),
                math.ceil(max(timeLst)) + 1,
                1
            )
        )

    # Declare Plot Components
    buttonBack = tk.Button(
        plot,
        height=configDict['buttonH'],
        width=configDict['buttonW'],
        text='Back',
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['color3'],
        fg=configDict['color1'],
        command=lambda: back(plot)
    )
    buttonClose = tk.Button(
        plot,
        height=configDict['buttonH'],
        width=configDict['buttonW'],
        text='Close',
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['color3'],
        fg=configDict['color1'],
        command=close
    )
    buttonAddProfile = tk.Button(
        plot,
        height=configDict['buttonH'],
        width=configDict['buttonW'],
        text='Add Profile',
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['color3'],
        fg=configDict['color1'],
        command=lambda: add_profile(
            timeLst,
            presLst
        )
    )
    labelTitle = tk.Label(
        plot,
        text='Extraction Performance: Temperature & Pressure Over Time',
        font=(
            configDict['font'],
            configDict['headerSize']
        ),
        bg=configDict['color4'],
        fg=configDict['color1']
    )
    labelStats = tk.Label(
        plot,
        text='Correl [%]:',
        font=(
            configDict['font'],
            configDict['labelSize']
        ),
        bg=configDict['color4'],
        fg=configDict['color1']
    )
    valueStats = tk.Label(
        plot,
        text=str(correl),
        font=(
            configDict['font'],
            configDict['labelSize'],
            'bold'
        ),
        bg=configDict['color4'],
        fg=configDict['color1']
    )
    canvas = FigureCanvasTkAgg(
        fig,
        master=plot
    )
    canvasPlot = canvas.get_tk_widget()
    labelXAxis = tk.Label(
        plot,
        text='Time [Sec.]',
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['color4'],
        fg=configDict['color1']
    )
    labelDuration = tk.Label(
        plot,
        text='Duration: '+str(max(timeLst))+' Sec.',
        font=(
            configDict['font'],
            configDict['labelSize']
        ),
        bg=configDict['color4'],
        fg=configDict['color1']
    )
    labelProfile = tk.Label(
        plot,
        text='Profile:',
        font=(
            configDict['font'],
            configDict['labelSize']
        ),
        bg=configDict['color4'],
        fg=configDict['color1']
    )
    valueProfile = tk.Label(
        plot,
        textvariable=tkProfile,
        font=(
            configDict['font'],
            configDict['labelSize'],
            'bold'
        ),
        bg=configDict['color4'],
        fg=configDict['color1']
    )

    # Pack Plot Components
    buttonBack.grid(
        column=0,
        row=0,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonClose.grid(
        column=6,
        row=0,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonAddProfile.grid(
        column=6,
        row=10,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    labelTitle.grid(
        column=1,
        row=0,
        columnspan=5,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.S+tk.E+tk.W
    )
    labelStats.grid(
        column=2,
        row=1,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    valueStats.grid(
        column=3,
        row=1,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    canvasPlot.grid(
        column=0,
        row=2,
        columnspan=7,
        rowspan=7,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.E+tk.W
    )
    labelXAxis.grid(
        column=2,
        row=9,
        columnspan=3,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.E+tk.W
    )
    labelDuration.grid(
        column=1,
        row=10,
        columnspan=2,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    labelProfile.grid(
        column=3,
        row=10,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    valueProfile.grid(
        column=4,
        row=10,
        columnspan=2,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.W
    )

# --------------------------------------------------
# Build Settings Frame
# --------------------------------------------------


def create_settings():
    global configDict, testEnv

    # Declare Settings Container
    settings = tk.Toplevel(
        master=root,
        width=800,
        height=480,
        background=configDict['color4']
    )
    settings.title('Settings')

    # Assign Environment Settings
    if not testEnv:
        settings.attributes('-fullscreen', True)
        settings.configure(cursor='none')

    for c in range(0, 7):
        settings.columnconfigure(
            c,
            minsize=114,
            weight=1
        )

    for r in range(0, 11):
        settings.rowconfigure(
            r,
            minsize=43,
            weight=1
        )

    # Check Profile Loc for Pressure Profile Configs
    if os.path.isdir(
        applicationLoc + dirSep +
        'config' + dirSep + 'profiles'
    ):
        profileLst = sorted(
            [
                item.split('.')[0]
                for item in os.listdir(
                    applicationLoc + dirSep +
                    'config' + dirSep + 'profiles'
                )
            ]
        )

    # Declare Settings Components
    buttonBack = tk.Button(
        settings,
        height=configDict['buttonH'],
        width=configDict['buttonW'],
        text='Back',
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['color3'],
        fg=configDict['color1'],
        command=lambda: save_settings(
            settings
        )
    )
    buttonClose = tk.Button(
        settings,
        height=configDict['buttonH'],
        width=configDict['buttonW'],
        text='Close',
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['color3'],
        fg=configDict['color1'],
        command=close
    )
    buttonDeleteProfile = tk.Button(
        settings,
        height=configDict['buttonH'],
        width=configDict['buttonW'],
        text='Delete Profile',
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['color3'],
        fg=configDict['color1'],
        command=lambda: delete_profile(
            selectProfile
        )
    )
    buttonUpdateProfile = tk.Button(
        settings,
        height=configDict['buttonH'],
        width=configDict['buttonW'],
        text='Edit Profile',
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['color3'],
        fg=configDict['color1'],
        command=lambda: create_profile(
            True
        )
    )
    buttonNewProfile = tk.Button(
        settings,
        height=configDict['buttonH'],
        width=configDict['buttonW'],
        text='New Profile',
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['color3'],
        fg=configDict['color1'],
        command=lambda: create_profile(
            False
        )
    )
    buttonRefresh = tk.Button(
        settings,
        height=configDict['buttonH'],
        width=configDict['buttonW'],
        text='Refresh',
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['color3'],
        fg=configDict['color1'],
        command=lambda: refresh_settings(
            selectProfile
        )
    )
    labelTHead = tk.Label(
        settings,
        textvariable=tkScale,
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['color4'],
        fg=configDict['color1']
    )
    labelOptnSetPoint = tk.Label(
        settings,
        text='Set-Point:',
        font=(
            configDict['font'],
            configDict['labelSize']
        ),
        bg=configDict['color4'],
        fg=configDict['color1'])
    selectSetPoint = tk.OptionMenu(
        settings,
        tkSetPoint,
        *setPointLst,
        command=setpoint_callback
    )
    labelOptnScale = tk.Label(
        settings,
        text='Scale:',
        font=(
            configDict['font'],
            configDict['labelSize']
        ),
        bg=configDict['color4'],
        fg=configDict['color1']
    )
    selectScale = tk.OptionMenu(
        settings,
        tkScale,
        *scaleLst,
        command=lambda value=tkScale,
        selectSetPoint=selectSetPoint,
        setPointLst=setPointLst: scale_callback(
            value,
            selectSetPoint,
            setPointLst
        )
    )
    labelPHead = tk.Label(
        settings,
        text='Pressure Profile',
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['color4'],
        fg=configDict['color1']
    )
    labelOptnProfile = tk.Label(
        settings,
        text='Profile:',
        font=(
            configDict['font'],
            configDict['labelSize']
        ),
        bg=configDict['color4'],
        fg=configDict['color1']
    )
    selectProfile = tk.OptionMenu(
        settings,
        tkProfile,
        *profileLst,
        command=profile_callback
    )
    labelFHead = tk.Label(
        settings,
        text='Flush [Sec.]',
        font=(
            configDict['font'],
            configDict['buttonSize']
        ),
        bg=configDict['color4'],
        fg=configDict['color1']
    )
    selectFlush = tk.OptionMenu(
        settings,
        tkFlush,
        *flushLst,
        command=flush_callback
    )
    labelOptnFlush = tk.Label(
        settings,
        text='Duration:',
        font=(
            configDict['font'],
            configDict['labelSize']
        ),
        bg=configDict['color4'],
        fg=configDict['color1']
    )

    # Apply MenuButton Style for all Dropdown Selections
    for optionMenu in [
        selectScale, selectSetPoint, selectProfile, selectFlush
    ]:
        optionMenu.configure(
            font=(
                configDict['font'],
                configDict['labelSize']
            ),
            bg=configDict['color3'],
            fg=configDict['color1'],
            relief=tk.FLAT
        )
        optionMenu['menu'].configure(
            font=(
                configDict['font'],
                configDict['labelSize']
            ),
            bg=configDict['color3'],
            fg=configDict['color1']
        )

    # Pack Settings Components
    buttonBack.grid(
        column=0,
        row=0,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonClose.grid(
        column=6,
        row=0,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonDeleteProfile.grid(
        column=3,
        row=4,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonUpdateProfile.grid(
        column=4,
        row=4,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonNewProfile.grid(
        column=5,
        row=4,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonRefresh.grid(
        column=0,
        row=10,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    labelTHead.grid(
        column=1,
        row=1,
        columnspan=2,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    labelOptnScale.grid(
        column=2,
        row=1,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    selectScale.grid(
        column=3,
        row=1,
        columnspan=3,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    labelOptnSetPoint.grid(
        column=2,
        row=2,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    selectSetPoint.grid(
        column=3,
        row=2,
        columnspan=3,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    labelPHead.grid(
        column=1,
        row=3,
        columnspan=2,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    labelOptnProfile.grid(
        column=2,
        row=3,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    selectProfile.grid(
        column=3,
        row=3,
        columnspan=3,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    labelFHead.grid(
        column=1,
        row=5,
        columnspan=2,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    labelOptnFlush.grid(
        column=2,
        row=5,
        columnspan=1,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    selectFlush.grid(
        column=3,
        row=5,
        columnspan=3,
        rowspan=1,
        padx=configDict['padX'],
        pady=configDict['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )

# --------------------------------------------------
# Build Profile Frame
# --------------------------------------------------


def create_profile(
    update
):
    global configDict, testEnv

    # Check if Manual Profile is Selected
    if (
        update and
        configDict['profile'].upper() == 'MANUAL'
    ):
        error('[Manual] profile cannot be modified.')
    else:
        # Declare Profile Container
        profile = tk.Toplevel(
            master=root,
            width=800,
            height=480,
            background=configDict['color4']
        )
        profile.title('Pressure Profile')

        # Assign Environment Settings
        if not testEnv:
            profile.attributes('-fullscreen', True)
            profile.configure(cursor='none')

        for c in range(0, 7):
            profile.columnconfigure(
                c,
                minsize=114,
                weight=1
            )

        for r in range(0, 11):
            profile.rowconfigure(
                r,
                minsize=43,
                weight=1
            )

        # Define Pressure Profile Function
        def calculate_profile_quartile(
            customDict,
            timeLst
        ):
            def calculate_slope(
                customDict,
                profLst,
                pStart,
                pEnd,
                tStart,
                tEnd
            ):
                # Calculate Slope
                num = pEnd - pStart
                denom = int(
                    (tEnd - tStart) * 10
                )
                m = float(num / denom)

                if pEnd == pStart:
                    profNew = [pEnd] * denom
                else:
                    profNew = [
                        round(item, 1)
                        for item in list(
                            np.arange(
                                pStart,
                                pEnd,
                                m
                            )
                        )
                    ]

                profLst += profNew

                return profLst

            # Create Pre-Infusion Profile
            profLst = []

            if customDict['infusionDuration'] == 0:
                profileMin = 0
            else:
                profileMin = int(
                    customDict['infusionDuration'] + 1
                )
                profLst = [
                    int(
                        customDict['infusionPressure']
                    )
                ] * customDict['infusionDuration'] * 10

                # Calculate Slope
                profLst = calculate_slope(
                    customDict,
                    profLst,
                    customDict['infusionPressure'],
                    customDict['p0'],
                    customDict['infusionDuration'],
                    profileMin
                )

            profileRange = list(
                np.arange(
                    profileMin,
                    int(
                        str(customDict['extractionDuration'])
                    ) + 1,
                    0.1
                )
            )

            # Create Extraction Profile
            q0 = float(round(np.quantile(profileRange, 0), 1))
            q1 = float(round(np.quantile(profileRange, .25), 1))
            q2 = float(round(np.quantile(profileRange, .5), 1))
            q3 = float(round(np.quantile(profileRange, .75), 1))
            q4 = float(round(np.quantile(profileRange, 1), 1))

            # Calculate Slope
            profLst = calculate_slope(
                customDict,
                profLst,
                customDict['p0'],
                customDict['p1'],
                q0,
                q1
            )
            profLst = calculate_slope(
                customDict,
                profLst,
                customDict['p1'],
                customDict['p2'],
                q1,
                q2
            )
            profLst = calculate_slope(
                customDict,
                profLst,
                customDict['p2'],
                customDict['p3'],
                q2,
                q3
            )
            profLst = calculate_slope(
                customDict,
                profLst,
                customDict['p3'],
                customDict['p4'],
                q3,
                q4
            )

            # Adjust Final Profile
            # Issue if Three Quartiles all Have the Same Pressure
            profLst.append(customDict['p4'])

            if len(profLst) != len(timeLst):
                profLst += [
                    customDict['p4']
                ] * int(
                    len(timeLst) - len(profLst)
                )

            # Assign Time Values for Scatter
            if customDict['infusionDuration'] == 0:
                scatterXLst = [q0, q1, q2, q3, q4]
            else:
                scatterXLst = [
                    0, customDict['infusionDuration'],
                    q0, q1, q2, q3, q4
                ]

            # Return Profile and Quartile for Scatter
            return profLst, scatterXLst

        # Create Pressure Profile Dictionary
        customDict = {}

        if os.path.isdir(
            applicationLoc + dirSep +
            'config' + dirSep + 'profiles'
        ):
            # Import Selected Profile
            if update:
                if os.path.isfile(
                    applicationLoc + dirSep +
                    'config' + dirSep + 'profiles' +
                    dirSep + configDict['profile'] + '.txt'
                ):
                    with open(
                        applicationLoc + dirSep +
                        'config' + dirSep + 'profiles' +
                        dirSep + configDict['profile'] + '.txt'
                    ) as file:
                        for line in file:
                            (var, val) = line.split('|')
                            try:
                                customDict[var] = int(val)
                            except ValueError:
                                customDict[var] = str(val).strip('\n')

                    # Convert to List
                    customDict['timeLst'] = ast.literal_eval(
                        customDict['timeLst']
                    )
                    customDict['profLst'] = ast.literal_eval(
                        customDict['profLst']
                    )

            # Create Custom Profile
            else:
                profileLst = [
                    item.split('.')[0]
                    for item in os.listdir(
                        applicationLoc + dirSep + 'config'
                        + dirSep + 'profiles'
                    )
                ]
                customProfiles = [
                    item for item in profileLst
                    if 'CUSTOM_' in item.upper()
                ]
                if customProfiles == []:
                    profileNum = 1
                else:
                    profileNum = int(
                        max(
                            int(item.split('_')[1])
                            for item in customProfiles
                        ) + 1
                    )

                customDict = {
                    'profileName': 'Custom_'+str(profileNum),
                    'extractionDuration': 25,
                    'infusionDuration': 3,
                    'infusionPressure': 3,
                    'p0': 9,
                    'p1': 9,
                    'p2': 9,
                    'p3': 9,
                    'p4': 9,
                    'timeLst': [],
                    'profLst': []
                }

        # Store Profile Dictionary Selections
        tkProfileName = tk.StringVar(root)
        tkProfileName.set(customDict['profileName'])

        tkExtractionDur = tk.IntVar(root)
        tkExtractionDur.set(customDict['extractionDuration'])

        tkInfusionDur = tk.IntVar(root)
        preDurDict = list(range(0, 11))
        tkInfusionDur.set(customDict['infusionDuration'])

        tkInfusionPres = tk.IntVar(root)
        prePresDict = list(range(1, 6))
        tkInfusionPres.set(customDict['infusionPressure'])

        tkP0 = tk.IntVar(root)
        tkP0.set(customDict['p0'])

        tkP1 = tk.IntVar(root)
        tkP1.set(customDict['p1'])

        tkP2 = tk.IntVar(root)
        tkP2.set(customDict['p2'])

        tkP3 = tk.IntVar(root)
        tkP3.set(customDict['p3'])

        tkP4 = tk.IntVar(root)
        tkP4.set(customDict['p4'])

        tkProfParams = tk.StringVar(root)
        tkProfParams.set(
            'Params: ' +
            str(tkExtractionDur.get()) +
            ' [Sec.], Pre-Inf. ' +
            str(tkInfusionDur.get()) +
            ' [Sec.] at ' +
            str(tkInfusionPres.get()) +
            ' [Bars], {P0:' +
            str(tkP0.get()) +
            ', P1:' +
            str(tkP1.get()) +
            ', P2:' +
            str(tkP2.get()) +
            ', P3:' +
            str(tkP3.get()) +
            ', P4:' +
            str(tkP4.get()) + '}'
        )

        # Create Time Series List
        timeLst = list(
            np.arange(
                0,
                int(customDict['extractionDuration'] + 1),
                0.1
            )
        )
        timeLst = [
            round(item, 1)
            for item in timeLst
        ]
        customDict['timeLst'] = timeLst

        # Return Initial Pressure Profile and Quartiles
        profLst, scatterXLst = calculate_profile_quartile(
            customDict,
            timeLst
        )
        customDict['profLst'] = profLst

        # Assign Pressure Values for Scatter
        if customDict['infusionDuration'] == 0:
            scatterYLst = [
                customDict['p0'],
                customDict['p1'],
                customDict['p2'],
                customDict['p3'],
                customDict['p4']
            ]
        else:
            scatterYLst = [
                customDict['infusionPressure'],
                customDict['infusionPressure'],
                customDict['p0'],
                customDict['p1'],
                customDict['p2'],
                customDict['p3'],
                customDict['p4']
            ]

        # Create Figure for Plot
        profFig = plt.figure()
        profFig.patch.set_facecolor(configDict['color4'])

        p1 = profFig.add_subplot(1, 1, 1)
        p1.set_facecolor(configDict['color3'])
        p2 = p1.twinx()

        for axes in [p1, p2]:
            for border in [
                'top', 'bottom', 'right', 'left'
            ]:
                axes.spines[border].set_color(configDict['color2'])

        # Get DPI and Assign Dimmensions to Figure
        DPI = float(profFig.get_dpi())
        profFig.set_size_inches(700 / DPI, 75 / DPI)

        # Clear, Format and Plot Temperature Values
        p1.clear()
        p1.set_ylabel(
            'Pressure [Bars]',
            color=configDict['red']
        )
        p1.set_xlim(
            min(timeLst),
            max(timeLst)
        )
        p1.set_ylim(
            0,
            12
        )
        p1.tick_params(
            axis='y',
            labelcolor=configDict['red'],
            labelsize=configDict['labelSize'] * 0.7,
            length=0,
            pad=10
        )
        p1.tick_params(
            axis='x',
            labelcolor=configDict['color1'],
            labelsize=configDict['labelSize'] * 0.7,
            length=0,
            pad=10
        )
        p1.grid(
            b=True,
            which='both',
            axis='both',
            color=configDict['color2'],
            linestyle='--',
            linewidth=1,
            alpha=0.5
        )
        p1.plot(
            timeLst,
            profLst,
            linewidth=2,
            color=configDict['red']
        )
        p1.set_xticks(
            ticks=np.arange(
                min(timeLst),
                math.ceil(max(timeLst)) + 1,
                1
            )
        )

        p2.clear()
        p2.set_ylim(0, 12)
        p2.scatter(
            scatterXLst,
            scatterYLst,
            c=configDict['red'],
            marker='s'
        )
        p2.set_yticks([])
        if max(timeLst) >= 40:
            p2.set_xticks(
                ticks=np.arange(
                    min(timeLst),
                    math.ceil(max(timeLst)) + 1,
                    2
                )
            )
        else:
            p2.set_xticks(
                ticks=np.arange(
                    min(timeLst),
                    math.ceil(max(timeLst)) + 1,
                    1
                )
            )
        profFig.subplots_adjust(bottom=0.15)

        # Define Callback Functions for Setting Dropdown Selections
        def plot_profile(
            value,
            tkProfParams,
            varDict,
            customDict,
            canvasProf,
            p1,
            p2
        ):
            # Update Profile Dictionary Value
            if varDict == 'profileName':
                customDict[varDict] = value
            else:
                customDict[varDict] = int(value)

            # Create Time Series List
            timeLst = list(
                np.arange(
                    0,
                    int(customDict['extractionDuration'] + 1),
                    0.1
                )
            )
            timeLst = [
                round(item, 1)
                for item in timeLst
            ]
            customDict['timeLst'] = timeLst

            # Return Pressure Profile and Quartiles
            profLst, scatterXLst = calculate_profile_quartile(
                customDict,
                timeLst
            )
            customDict['profLst'] = profLst

            # Assign Pressure Values for Scatter
            if customDict['infusionDuration'] == 0:
                scatterYLst = [
                    customDict['p0'],
                    customDict['p1'],
                    customDict['p2'],
                    customDict['p3'],
                    customDict['p4']
                ]
            else:
                scatterYLst = [
                    customDict['infusionPressure'],
                    customDict['infusionPressure'],
                    customDict['p0'],
                    customDict['p1'],
                    customDict['p2'],
                    customDict['p3'],
                    customDict['p4']
                ]

            # Update Parameter Label
            tkProfParams.set(
                'Params: ' +
                str(customDict['extractionDuration']) +
                ' [Sec.], Pre-Inf. ' +
                str(customDict['infusionDuration']) +
                ' [Sec.] at ' +
                str(customDict['infusionPressure']) +
                ' [Bars], {P0:' +
                str(customDict['p0']) +
                ', P1:' +
                str(customDict['p1']) +
                ', P2:' +
                str(customDict['p2']) +
                ', P3:' +
                str(customDict['p3']) +
                ', P4:' +
                str(customDict['p4']) + '}'
            )

            # Clear, Format and Plot Temperature Values
            p1.clear()
            p1.set_ylabel(
                'Pressure [Bars]',
                color=configDict['red']
            )
            p1.set_xlim(
                min(timeLst),
                max(timeLst)
            )
            p1.set_ylim(
                0,
                12
            )
            p1.tick_params(
                axis='y',
                labelcolor=configDict['red'],
                labelsize=configDict['labelSize'] * 0.7,
                length=0,
                pad=10
            )
            p1.tick_params(
                axis='x',
                labelcolor=configDict['color1'],
                labelsize=configDict['labelSize'] * 0.7,
                length=0,
                pad=10
            )
            p1.grid(
                b=True,
                which='both',
                axis='both',
                color=configDict['color2'],
                linestyle='--',
                linewidth=1,
                alpha=0.5
            )
            p1.plot(
                timeLst,
                profLst,
                linewidth=2,
                color=configDict['red']
            )

            p2.clear()
            p2.set_ylim(
                0,
                12
            )
            p2.scatter(
                scatterXLst,
                scatterYLst,
                c=configDict['red'],
                marker='s'
            )
            p2.set_yticks([])
            if max(timeLst) >= 40:
                p2.set_xticks(
                    ticks=np.arange(
                        min(timeLst),
                        math.ceil(max(timeLst)) + 1,
                        2
                    )
                )
            else:
                p2.set_xticks(
                    ticks=np.arange(
                        min(timeLst),
                        math.ceil(max(timeLst)) + 1,
                        1
                    )
                )
            profFig.subplots_adjust(bottom=0.15)

            # Update the Canvas
            canvasProf.draw()

        # Declare Profile Components
        canvasProf = FigureCanvasTkAgg(
            profFig,
            master=profile
        )
        canvasProfile = canvasProf.get_tk_widget()
        buttonBack = tk.Button(
            profile,
            height=configDict['buttonH'],
            width=configDict['buttonW'],
            text='Back',
            font=(
                configDict['font'],
                configDict['buttonSize']
            ),
            bg=configDict['color3'],
            fg=configDict['color1'],
            command=lambda: back(profile)
        )
        buttonClose = tk.Button(
            profile,
            height=configDict['buttonH'],
            width=configDict['buttonW'],
            text='Close',
            font=(
                configDict['font'],
                configDict['buttonSize']
            ),
            bg=configDict['color3'],
            fg=configDict['color1'],
            command=close
        )
        buttonSave = tk.Button(
            profile,
            height=configDict['buttonH'],
            width=configDict['buttonW'],
            text='Save',
            font=(
                configDict['font'],
                configDict['buttonSize']
            ),
            bg=configDict['color3'],
            fg=configDict['color1'],
            command=lambda: check_profile(
                profile,
                customDict,
                tkProfileName
            )
        )
        labelProfileName = tk.Label(
            profile,
            text='Profile Name:',
            font=(
                configDict['font'],
                configDict['labelSize']
            ),
            bg=configDict['color4'],
            fg=configDict['color1']
        )
        valueProfileName = tk.Entry(
            profile,
            textvariable=tkProfileName,
            font=(
                configDict['font'],
                configDict['labelSize'],
                'bold'
            ),
            bg=configDict['color3'],
            fg=configDict['color1']
        )
        labelExtractionDur = tk.Label(
            profile,
            text='Extraction Duration [Sec.]:',
            font=(
                configDict['font'],
                configDict['labelSize']
            ),
            bg=configDict['color4'],
            fg=configDict['color1']
        )
        valueExtractionDur = tk.Scale(
            profile,
            from_=12,
            to=60,
            variable=tkExtractionDur,
            orient=tk.HORIZONTAL,
            showvalue=0,
            font=(
                configDict['font'],
                configDict['labelSize'],
                'bold'
            ),
            bg=configDict['color3'],
            fg=configDict['color1'],
            troughcolor=configDict['color2'],
            command=lambda value=tkExtractionDur,
            tkProfParams=tkProfParams,
            varDict='extractionDuration',
            customDict=customDict,
            canvasProf=canvasProf,
            p1=p1,
            p2=p2: plot_profile(
                value,
                tkProfParams,
                varDict,
                customDict,
                canvasProf,
                p1,
                p2
            )
        )
        labelPreInfusion = tk.Label(
            profile,
            text='Pre-Infusion:',
            font=(
                configDict['font'],
                configDict['labelSize']
            ),
            bg=configDict['color4'],
            fg=configDict['color1']
        )
        labelPreDur = tk.Label(
            profile,
            text='Duration [Sec.]:',
            font=(
                configDict['font'],
                configDict['labelSize']
            ),
            bg=configDict['color4'],
            fg=configDict['color1']
        )
        valuePreDur = tk.OptionMenu(
            profile,
            tkInfusionDur,
            *preDurDict,
            command=lambda value=tkInfusionDur,
            tkProfParams=tkProfParams,
            varDict='infusionDuration',
            customDict=customDict,
            canvasProf=canvasProf,
            p1=p1,
            p2=p2: plot_profile(
                value,
                tkProfParams,
                varDict,
                customDict,
                canvasProf,
                p1,
                p2
            )
        )
        labelPrePres = tk.Label(
            profile,
            text='Pressure [Bars]:',
            font=(
                configDict['font'],
                configDict['labelSize']
            ),
            bg=configDict['color4'],
            fg=configDict['color1']
        )
        valuePrePres = tk.OptionMenu(
            profile,
            tkInfusionPres,
            *prePresDict,
            command=lambda value=tkInfusionPres,
            tkProfParams=tkProfParams,
            varDict='infusionPressure',
            customDict=customDict,
            canvasProf=canvasProf,
            p1=p1,
            p2=p2: plot_profile(
                value,
                tkProfParams,
                varDict,
                customDict,
                canvasProf,
                p1,
                p2
            )
        )
        labelP0 = tk.Label(
            profile,
            text='P0:',
            font=(
                configDict['font'],
                configDict['labelSize']
            ),
            bg=configDict['color4'],
            fg=configDict['color1']
        )
        valueP0 = tk.Scale(
            profile,
            from_=1,
            to=12,
            variable=tkP0,
            orient=tk.HORIZONTAL,
            showvalue=0,
            font=(
                configDict['font'],
                configDict['labelSize'],
                'bold'
            ),
            bg=configDict['color3'],
            fg=configDict['color1'],
            troughcolor=configDict['color2'],
            command=lambda value=tkP0,
            tkProfParams=tkProfParams,
            varDict='p0',
            customDict=customDict,
            canvasProf=canvasProf,
            p1=p1,
            p2=p2: plot_profile(
                value,
                tkProfParams,
                varDict,
                customDict,
                canvasProf,
                p1,
                p2
            )
        )
        labelP1 = tk.Label(
            profile,
            text='P1:',
            font=(
                configDict['font'],
                configDict['labelSize']
            ),
            bg=configDict['color4'],
            fg=configDict['color1']
        )
        valueP1 = tk.Scale(
            profile,
            from_=1,
            to=12,
            variable=tkP1,
            orient=tk.HORIZONTAL,
            showvalue=0,
            font=(
                configDict['font'],
                configDict['labelSize'],
                'bold'
            ),
            bg=configDict['color3'],
            fg=configDict['color1'],
            troughcolor=configDict['color2'],
            command=lambda value=tkP1,
            tkProfParams=tkProfParams,
            varDict='p1',
            customDict=customDict,
            canvasProf=canvasProf,
            p1=p1,
            p2=p2: plot_profile(
                value,
                tkProfParams,
                varDict,
                customDict,
                canvasProf,
                p1,
                p2
            )
        )
        labelP2 = tk.Label(
            profile,
            text='P2:',
            font=(
                configDict['font'],
                configDict['labelSize']
            ),
            bg=configDict['color4'],
            fg=configDict['color1']
        )
        valueP2 = tk.Scale(
            profile,
            from_=1,
            to=12,
            variable=tkP2,
            orient=tk.HORIZONTAL,
            showvalue=0,
            font=(
                configDict['font'],
                configDict['labelSize'],
                'bold'
            ),
            bg=configDict['color3'],
            fg=configDict['color1'],
            troughcolor=configDict['color2'],
            command=lambda value=tkP2,
            tkProfParams=tkProfParams,
            varDict='p2',
            customDict=customDict,
            canvasProf=canvasProf,
            p1=p1,
            p2=p2: plot_profile(
                value,
                tkProfParams,
                varDict,
                customDict,
                canvasProf,
                p1,
                p2
            )
        )
        labelP3 = tk.Label(
            profile,
            text='P3:',
            font=(
                configDict['font'],
                configDict['labelSize']
            ),
            bg=configDict['color4'],
            fg=configDict['color1']
        )
        valueP3 = tk.Scale(
            profile,
            from_=1,
            to=12,
            variable=tkP3,
            orient=tk.HORIZONTAL,
            showvalue=0,
            font=(
                configDict['font'],
                configDict['labelSize'],
                'bold'
            ),
            bg=configDict['color3'],
            fg=configDict['color1'],
            troughcolor=configDict['color2'],
            command=lambda value=tkP3,
            tkProfParams=tkProfParams,
            varDict='p3',
            customDict=customDict,
            canvasProf=canvasProf,
            p1=p1,
            p2=p2: plot_profile(
                value,
                tkProfParams,
                varDict,
                customDict,
                canvasProf,
                p1,
                p2
            )
        )
        labelP4 = tk.Label(
            profile,
            text='P4:',
            font=(
                configDict['font'],
                configDict['labelSize']
            ),
            bg=configDict['color4'],
            fg=configDict['color1']
        )
        valueP4 = tk.Scale(
            profile,
            from_=1,
            to=12,
            variable=tkP4,
            orient=tk.HORIZONTAL,
            showvalue=0,
            font=(
                configDict['font'],
                configDict['labelSize'],
                'bold'
            ),
            bg=configDict['color3'],
            fg=configDict['color1'],
            troughcolor=configDict['color2'],
            command=lambda value=tkP4,
            tkProfParams=tkProfParams,
            varDict='p4',
            customDict=customDict,
            canvasProf=canvasProf,
            p1=p1,
            p2=p2: plot_profile(
                value,
                tkProfParams,
                varDict,
                customDict,
                canvasProf,
                p1,
                p2
            )
        )
        labelParams = tk.Label(
            profile,
            textvariable=tkProfParams,
            font=(
                configDict['font'],
                configDict['labelSize']
            ),
            bg=configDict['color4'],
            fg=configDict['color1']
        )

        # Apply MenuButton Style for all Dropdown Selections
        for optionMenu in [
            valuePreDur, valuePrePres
        ]:
            optionMenu.configure(
                font=(
                    configDict['font'],
                    configDict['labelSize']
                ),
                bg=configDict['color3'],
                fg=configDict['color1'],
                relief=tk.FLAT
            )
            optionMenu['menu'].configure(
                font=(
                    configDict['font'],
                    configDict['labelSize']
                ),
                bg=configDict['color3'],
                fg=configDict['color1']
            )

        # Pack Profile Components
        buttonBack.grid(
            column=0,
            row=0,
            columnspan=1,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        buttonClose.grid(
            column=6,
            row=0,
            columnspan=1,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        buttonSave.grid(
            column=6,
            row=10,
            columnspan=1,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        canvasProfile.grid(
            column=0,
            row=1,
            columnspan=7,
            rowspan=4,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        labelProfileName.grid(
            column=1,
            row=5,
            columnspan=1,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E
        )
        valueProfileName.grid(
            column=2,
            row=5,
            columnspan=2,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        labelExtractionDur.grid(
            column=0,
            row=6,
            columnspan=2,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E
        )
        valueExtractionDur.grid(
            column=2,
            row=6,
            columnspan=2,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        labelPreInfusion.grid(
            column=1,
            row=7,
            columnspan=1,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E
        )
        labelPreDur.grid(
            column=2,
            row=7,
            columnspan=1,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E
        )
        valuePreDur.grid(
            column=3,
            row=7,
            columnspan=1,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        labelPrePres.grid(
            column=2,
            row=8,
            columnspan=1,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E
        )
        valuePrePres.grid(
            column=3,
            row=8,
            columnspan=1,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        labelP0.grid(
            column=4,
            row=5,
            columnspan=1,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E
        )
        valueP0.grid(
            column=5,
            row=5,
            columnspan=2,
            rowspan=1,
            padx=configDict['padX'] + 10,
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        labelP1.grid(
            column=4,
            row=6,
            columnspan=1,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E
        )
        valueP1.grid(
            column=5,
            row=6,
            columnspan=2,
            rowspan=1,
            padx=configDict['padX'] + 10,
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        labelP2.grid(
            column=4,
            row=7,
            columnspan=1,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E
        )
        valueP2.grid(
            column=5,
            row=7,
            columnspan=2,
            rowspan=1,
            padx=configDict['padX'] + 10,
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        labelP3.grid(
            column=4,
            row=8,
            columnspan=1,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E
        )
        valueP3.grid(
            column=5,
            row=8,
            columnspan=2,
            rowspan=1,
            padx=configDict['padX'] + 10,
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        labelP4.grid(
            column=4,
            row=9,
            columnspan=1,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E
        )
        valueP4.grid(
            column=5,
            row=9,
            columnspan=2,
            rowspan=1,
            padx=configDict['padX'] + 10,
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        labelParams.grid(
            column=0,
            row=10,
            columnspan=6,
            rowspan=1,
            padx=configDict['padX'],
            pady=configDict['padY'],
            sticky=tk.N+tk.S+tk.W
        )

# --------------------------------------------------
# Build Root TK Object
# --------------------------------------------------


root = tk.Tk()


root.title('Sprata')

# Assign Environment Settings
if not testEnv:
    root.attributes('-fullscreen', True)
    root.configure(cursor='none')

# Declare Main Container
mainFrame = tk.Frame(
    root,
    width=800,
    height=480,
    background=configDict['color4']
)
mainFrame.pack(
    fill=tk.BOTH,
    expand=True
)

for c in range(0, 7):
    mainFrame.columnconfigure(
        c,
        minsize=114,
        weight=1
    )

for r in range(0, 11):
    mainFrame.rowconfigure(
        r,
        minsize=43,
        weight=1
    )

# Store config Dictionary Selections
tkCounter = tk.DoubleVar(root)
tkCounter.set(float(counter))

tkScale = tk.StringVar(root)
scaleLst = ['Fahrenheit [F]', 'Celcius [C]']
tkScale.set(configDict['scale'])

tkSetPoint = tk.IntVar(root)

# Assign Temperature Range Based on Scale Value
if configDict['scale'].split(' ')[1] == '[F]':
    setPointLst = list(np.arange(205, 226, 1))
else:
    setPointLst = [
        round(item, 1)
        for item in list(
            np.arange(96, 109, 0.5)
        )
    ]

tkSetPoint.set(configDict['setPoint'])

tkProfile = tk.StringVar(root)

# Check Profile Loc for Pressure Profile Configs
if os.path.isdir(
    applicationLoc + dirSep +
    'config' + dirSep + 'profiles'
):
    profileLst = sorted(
        [
            item.split('.')[0]
            for item in os.listdir(
                applicationLoc + dirSep +
                'config' + dirSep + 'profiles'
            )
        ]
    )
else:
    print(
        'ERROR: ' + applicationLoc + dirSep +
        'config' + dirSep + 'Profiles Does Not Exist.'
    )
    exit()

# Check if configDict Profile Exists within Profile Loc
if configDict['profile'] not in profileLst:

    # Check if Manual Profile Exists within Profile Loc
    if 'Manual' not in profileLst:
        manualDict = {
            'profileName': 'Manual',
            'extractionDuration': 0,
            'infusionDuration': 0,
            'infusionPressure': 0,
            'p0': 0,
            'p1': 0,
            'p2': 0,
            'p3': 0,
            'p4': 0,
            'tempLst': '[]',
            'profLst': '[]'
        }

        # Write out Manual Profile
        with open(
            applicationLoc + dirSep +
            'config' + dirSep + 'profiles' +
            dirSep + 'Manual.txt',
            mode='w',
            newline=''
        ) as file:
            profileWriter = csv.writer(
                file,
                delimiter='|'
            )

            for var, val in manualDict.items():
                profileWriter.writerow([var, val])

    # Set configDict parameter to Manual
    configDict['profile'] = 'Manual'

    # Write config Changes
    with open(
        applicationLoc + dirSep +
        'config' + dirSep + 'config.txt',
        mode='w',
        newline=''
    ) as file:
        configWriter = csv.writer(
            file,
            delimiter='|'
        )

        for var, val in configDict.items():
            configWriter.writerow([var, val])

tkProfile.set(configDict['profile'])

tkFlush = tk.IntVar(root)
flushLst = list(range(1, 6))
tkFlush.set(configDict['flush'])

# Set Initial Sensor Values
tkTempValue = tk.IntVar(root)
tkTempValue.set(read_temp())

tkPresValue = tk.DoubleVar(root)
tkPresValue.set(read_pressure())

# Declare Main Components
buttonClose = tk.Button(
    mainFrame,
    height=configDict['buttonH'],
    width=configDict['buttonW'],
    text='Close',
    font=(
        configDict['font'],
        configDict['buttonSize']
    ),
    bg=configDict['color3'],
    fg=configDict['color1'],
    command=close
)
buttonPower = tk.Button(
    mainFrame,
    height=configDict['buttonH'] * 2,
    width=configDict['buttonW'],
    text='Power',
    font=(
        configDict['font'],
        configDict['buttonSize']
    ),
    bg=configDict['color3'],
    fg=configDict['color1'],
    command=button_press,
    state=tk.DISABLED
)
buttonDash = tk.Button(
    mainFrame,
    height=configDict['buttonH'] * 2,
    width=configDict['buttonW'],
    text='Dashboard',
    font=(
        configDict['font'],
        configDict['buttonSize']
    ),
    bg=configDict['color3'],
    fg=configDict['color1'],
    command=create_dashboard
)
buttonSettings = tk.Button(
    mainFrame,
    height=configDict['buttonH'] * 2,
    width=configDict['buttonW'],
    text='Settings',
    font=(
        configDict['font'],
        configDict['buttonSize']
    ),
    bg=configDict['color3'],
    fg=configDict['color1'],
    command=create_settings
)
labelTemp = tk.Label(
    mainFrame,
    textvariable=tkScale,
    font=(
        configDict['font'],
        configDict['labelSize']
    ),
    bg=configDict['color4'],
    fg=configDict['color1']
)
valueTemp = tk.Label(
    mainFrame,
    textvariable=tkTempValue,
    font=(
        configDict['font'],
        configDict['labelSize'],
        'bold'
    ),
    bg=configDict['color4'],
    fg=configDict['blue']
)
labelPres = tk.Label(
    mainFrame,
    text='Pressure [Bars]',
    font=(
        configDict['font'],
        configDict['labelSize']
    ),
    bg=configDict['color4'],
    fg=configDict['color1']
)
valuePres = tk.Label(
    mainFrame,
    textvariable=tkPresValue,
    font=(
        configDict['font'],
        configDict['labelSize'],
        'bold'
    ),
    bg=configDict['color4'],
    fg=configDict['red']
)
labelProfile = tk.Label(
    mainFrame,
    text='Profile:',
    font=(
        configDict['font'],
        configDict['labelSize']
    ),
    bg=configDict['color4'],
    fg=configDict['color1']
)
valueProfile = tk.Label(
    mainFrame,
    textvariable=tkProfile,
    font=(
        configDict['font'],
        configDict['labelSize'],
        'bold'
    ),
    bg=configDict['color4'],
    fg=configDict['color1']
)

# Pack Main Components
buttonClose.grid(
    column=6,
    row=0,
    columnspan=1,
    rowspan=1,
    padx=configDict['padX'],
    pady=configDict['padY'],
    sticky=tk.N+tk.S+tk.E+tk.W
)
buttonPower.grid(
    column=2,
    row=7,
    columnspan=1,
    rowspan=2,
    padx=configDict['padX'],
    pady=configDict['padY'],
    sticky=tk.N+tk.S+tk.E+tk.W
)
buttonDash.grid(
    column=3,
    row=7,
    columnspan=1,
    rowspan=2,
    padx=configDict['padX'],
    pady=configDict['padY'],
    sticky=tk.N+tk.S+tk.E+tk.W
)
buttonSettings.grid(
    column=4,
    row=7,
    columnspan=1,
    rowspan=2,
    padx=configDict['padX'],
    pady=configDict['padY'],
    sticky=tk.N+tk.S+tk.E+tk.W
)
buttonClose.grid(
    column=6,
    row=0,
    columnspan=1,
    rowspan=1,
    padx=configDict['padX'],
    pady=configDict['padY'],
    sticky=tk.N+tk.S+tk.E+tk.W
)
labelTemp.grid(
    column=0,
    row=10,
    columnspan=1,
    rowspan=1,
    padx=configDict['padX'],
    pady=configDict['padY'],
    sticky=tk.N+tk.S+tk.E
)
valueTemp.grid(
    column=1,
    row=10,
    columnspan=1,
    rowspan=1,
    padx=configDict['padX'],
    pady=configDict['padY'],
    sticky=tk.N+tk.S+tk.W
)
labelPres.grid(
    column=2,
    row=10,
    columnspan=1,
    rowspan=1,
    padx=configDict['padX'],
    pady=configDict['padY'],
    sticky=tk.N+tk.S+tk.E
)
valuePres.grid(
    column=3,
    row=10,
    columnspan=1,
    rowspan=1,
    padx=configDict['padX'],
    pady=configDict['padY'],
    sticky=tk.N+tk.S+tk.W
)
labelProfile.grid(
    column=4,
    row=10,
    columnspan=1,
    rowspan=1,
    padx=configDict['padX'],
    pady=configDict['padY'],
    sticky=tk.N+tk.S+tk.E
)
valueProfile.grid(
    column=5,
    row=10,
    columnspan=2,
    rowspan=1,
    padx=configDict['padX'],
    pady=configDict['padY'],
    sticky=tk.N+tk.S+tk.W
)

# Run
root.after(100, idle)
root.mainloop()
