"""
Information
---------------------------------------------------------------------
Name        : dashboard.py
Location    : ~/modules/
Author      : Tom Eleff
Published   : 2023-06-25
Revised on  : .

Description
---------------------------------------------------------------------
Runs the GUI application.
"""

# Import modules
import os
import sys
import re
import math
import tkinter as tk
import customtkinter
import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.stats import pearsonr

import utils.utils as utils
import sensors.temp as temp
import sensors.pressure as pressure

# Initialize global variables
idling = True
running = False
flashing = False
counter = 0
temperatureLst = []
pressureLst = []
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
        GPIO.OUT
    )

# Initialize temperatore sensor
tSensor = temp.Sensor(
    outputPin=config['tPID']['pin']
)
tSensor.initialize(config)

# Initialize pressure sensor
pSensor = pressure.Sensor(
    outputPin=config['pPID']['pin']
)
pSensor.initialize(config)

# Assign extraction ID
if os.path.isdir(config['session']['diagnosticsLoc']):
    databaseLst = os.listdir(config['session']['diagnosticsLoc'])
    databaseLst = [
        item for item in databaseLst if ('Diagnostics_' and '.csv') in item
    ]

    # If no diagnostic files exists, then re-assign the ID
    if databaseLst == []:
        uniqueID = 1

    # If diagnostic files exist, then assign as max(ID)
    else:
        uniqueID = int(
            max([
                int(Item.split('_')[1]) for Item in databaseLst
            ]) + 1
        )
else:
    print('ERROR: Invalid Diagnostics Location Provided in config.')
    print(
        '       Please Provide Real Directory Path for %s.' % (
            config['session']['diagnosticsLoc']
        )
    )
    sys.exit()


# Define application navigation functions
def button_press():
    """
    Variables
    ---------------------------------------------------------------------

    Description
    ---------------------------------------------------------------------

    """

    print('Click')


def error(
    message
):
    """
    Variables
    ---------------------------------------------------------------------
    message                 = <str> Text to display in the error frame

    Description
    ---------------------------------------------------------------------
    Raises an error frame object.
    """

    # Create error frame
    error = create_toplevel_frame(
        master=root,
        title='Error',
        width=342,
        height=129,
        numCols=4,
        numRows=4,
        fullscreen=False
    )

    # Declare error frame components
    labelError = customtkinter.CTkLabel(
        error,
        text=' '.join(
            ['Error:', message]
        )
    )
    buttonOkay = customtkinter.CTkButton(
        error,
        height=config['format']['buttonHeight'],
        width=config['format']['buttonWidth'],
        corner_radius=config['format']['buttonHeight'],
        text='Okay',
        command=lambda: back(error)
    )

    # Pack error frame components
    labelError.grid(
        column=0,
        row=0,
        columnspan=3,
        rowspan=2,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonOkay.grid(
        column=2,
        row=2,
        columnspan=2,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )


def close():
    """
    Variables
    ---------------------------------------------------------------------

    Description
    ---------------------------------------------------------------------
    Closes the root window object.
    """

    global idling, running, flashing

    idling = False
    running = False
    flashing = False

    # Exit
    root.destroy()
    sys.exit()


def back(
    frame
):
    """
    Variables
    ---------------------------------------------------------------------
    frame                   = <class> CTkFrame object to close

    Description
    ---------------------------------------------------------------------
    Closes a frame object.
    """

    # Close the top-frame to reveal the previous frame
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
    """
    Variables
    ---------------------------------------------------------------------
    labelCounter            = <class> CTkLabel object
    buttonStart             = <class> CTkButton object
    buttonStop              = <class> CTkButton object
    buttonReset             = <class> CTkButton object
    buttonPlot              = <class> CTkButton object
    buttonSave              = <class> CTkButton object
    buttonSettings          = <class> CTkButton object
    buttonBack              = <class> CTkButton object

    Description
    ---------------------------------------------------------------------
    Writes the espresso extraction data to the ~/diagnostics/ folder and
    re-sets the state of {labelCounter}, {buttonStart}, {buttonStop},
    {buttonReset}, {buttonPlot}, {buttonSave}, {buttonSettings}, and
    {buttonBack}.
    """

    global idling, running, flashing
    global counter, temperatureLst, pressureLst, uniqueID
    global tkCounter, tkTempValue, tkPresValue

    # Initialize the extraction dataframe
    extractionDf = pd.DataFrame()

    # Generate a time series list
    timeLst = [
        round(item / 10, 1)
        for item in list(
            range(
                0,
                len(temperatureLst)
            )
        )
    ]

    # Read pressure profile config
    profile = read_profile(
        profileName=config['settings']['profile']
    )

    # Generate extraction data series
    username = [
        ', '.join([
            config['user']['last'],
            config['user']['first']
        ])
    ] * len(temperatureLst)
    uniqueIDLst = [uniqueID] * len(temperatureLst)
    date = [
        dt.datetime.now().strftime('%d/%b/%Y').upper()
    ] * len(temperatureLst)
    time = [
        dt.datetime.now().strftime('%H:%M:%S')
    ] * len(temperatureLst)
    tUnit = [
        config['settings']['scale']
    ] * len(temperatureLst)
    pUnit = ['Bars'] * len(temperatureLst)
    maxDuration = [max(timeLst)] * len(temperatureLst)
    minTemp = [min(temperatureLst)] * len(temperatureLst)
    maxTemp = [max(temperatureLst)] * len(temperatureLst)
    minPressure = [min(pressureLst)] * len(temperatureLst)
    maxPressure = [max(pressureLst)] * len(temperatureLst)
    tempSetPoint = [config['tPID']['setPoint']] * len(temperatureLst)

    if config['settings']['profile'].upper().strip() == 'MANUAL':
        profileName = [config['settings']['profile']] * len(temperatureLst)
        presProf = [0] * len(temperatureLst)
    else:
        profileName = [config['settings']['profile']] * len(temperatureLst)
        presProf = profile['settings']['pressureProfileLst']

    # Build dataframe from extraction data series'
    extractionDf = pd.DataFrame(
        data={
            'User': username,
            'UniqueID': uniqueIDLst,
            'Date': date,
            'Time': time,
            'Duration': timeLst,
            'Temperature': temperatureLst,
            'TUnit': tUnit,
            'Pressure': pressureLst,
            'PUnit': pUnit,
            'MaxDuration': maxDuration,
            'MinTemp': minTemp,
            'MaxTemp': maxTemp,
            'MinPressure': minPressure,
            'MaxPressure': maxPressure,
            'TempSetPoint': tempSetPoint,
            'Profile': profileName,
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

    # Output dataframe
    extractionDf.to_csv(
        os.path.join(
            config['session']['diagnosticsLoc'],
            '.'.join([
                '_'.join([
                    'Diagnostics',
                    str(uniqueID),
                    date[0].replace('/', '')
                ]),
                'csv'
            ])
        ),
        sep=',',
        index=False
    )

    # Configure application state
    idling = True
    running = False
    flashing = False
    counter = 0
    temperatureLst = []
    pressureLst = []

    # Update application components
    tkCounter.set(float(round(counter / 10, 1)))
    tkTempValue.set(tSensor.read_temp(config))
    tkPresValue.set(pSensor.read_pressure(config))

    labelCounter.configure(text_color=theme['CTkLabel']['text_color'])
    buttonStart.configure(state='normal')
    buttonStop.configure(state='disabled')
    buttonReset.configure(state='disabled')
    buttonPlot.configure(state='disabled')
    buttonSave.configure(state='disabled')
    buttonSettings.configure(state='normal')
    buttonBack.configure(state='normal')

    # Trigger idling
    idle()


def save_settings(
    frame
):
    """
    Variables
    ---------------------------------------------------------------------
    frame                   = <class> CTkFrame object to close

    Description
    ---------------------------------------------------------------------
    Writes the config dictionary object to ~/config/config.json and
    closes the frame.
    """

    # Write config
    try:
        utils.write_config(
            configLoc=os.path.join(
                config['session']['configLoc'], 'config.json'
            ),
            config=config
        )
    except FileNotFoundError as e:
        print(e)
        sys.exit()

    # Close the top-level frame
    frame.destroy()


def read_profile(
    profileName
):
    """
    Variables
    ---------------------------------------------------------------------
    profileName             = <str> Name of a pressure profile config

    Description
    ---------------------------------------------------------------------
    Reads and validates a pressure profile config.
    """

    # Read pressure profile config
    try:
        profile = utils.read_config(
                configLoc=os.path.join(
                    config['session']['configLoc'],
                    'profiles',
                    '.'.join([
                        profileName,
                        'json'
                    ])
                )
            )
    except (FileNotFoundError, IOError) as e:
        print(e)
        sys.exit()

    # Read dtypes config
    try:
        dtype = utils.read_config(
                configLoc=os.path.join(
                    config['session']['configLoc'],
                    'profiles',
                    'dtypes.json'
                )
            )
    except FileNotFoundError as e:
        print(e)
        sys.exit()

    # Validate pressure profile config
    try:
        utils.validate_config(
            profile,
            dtype
        )
    except TypeError as e:
        print(e)
        sys.exit()

    return profile


def check_profile(
    frame,
    customProfile,
    tkProfileName
):
    """
    Variables
    ---------------------------------------------------------------------
    frame                   = <class> CTkFrame object to close
    customProfile           = <dict> Dictionary object of the espresso
                                profile settings
    tkProfileName           = <class> CTkLabel object

    Description
    ---------------------------------------------------------------------
    Validates the {customProfile} dictionary object and writes the
    pressure profile config object to ~/config/profiles/.
    """

    # Update profile name value
    customProfile['settings']['profileName'] = tkProfileName.get()

    # Check if profile name already exists
    if os.path.isdir(
        os.path.join(
            config['session']['configLoc'],
            'profiles'
        )
    ):
        profileLst = sorted(
            [
                item.split('.')[0] for item in os.listdir(
                    os.path.join(
                        config['session']['configLoc'],
                        'profiles'
                    )
                ) if (
                    (item.split('.')[0].upper().strip() != 'DTYPES') and
                    (item.split('.')[1].upper() == 'JSON')
                )
            ]
        )

    if customProfile['settings']['profileName'] in profileLst:

        # Create warning frame
        warning = create_toplevel_frame(
            master=root,
            title='Warning',
            width=342,
            height=129,
            numCols=4,
            numRows=4,
            fullscreen=False
        )

        # Define warning messages
        message0 = '[%s] already exists.' % (
            customProfile['settings']['profileName']
        )
        message1 = 'Do you want to overwrite it?'

        # Declare warning frame components
        labelWarning0 = customtkinter.CTkLabel(
            warning,
            text=message0
        )
        labelWarning1 = customtkinter.CTkLabel(
            warning,
            text=message1
        )
        buttonNo = customtkinter.CTkButton(
            warning,
            height=config['format']['buttonHeight'],
            width=config['format']['buttonWidth'],
            corner_radius=config['format']['buttonHeight'],
            text='No',
            command=lambda: back(warning)
        )
        buttonYes = customtkinter.CTkButton(
            warning,
            height=config['format']['buttonHeight'],
            width=config['format']['buttonWidth'],
            corner_radius=config['format']['buttonHeight'],
            text='Yes',
            command=lambda: save_profile(
                frame,
                customProfile,
                True,
                warning
            )
        )

        # Pack warning frame components
        labelWarning0.grid(
            column=0,
            row=0,
            columnspan=3,
            rowspan=1,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.W
        )
        labelWarning1.grid(
            column=0,
            row=1,
            columnspan=3,
            rowspan=1,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        buttonNo.grid(
            column=0,
            row=2,
            columnspan=2,
            rowspan=1,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.W
        )
        buttonYes.grid(
            column=2,
            row=2,
            columnspan=2,
            rowspan=1,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E
        )

    else:
        # Set empty warning frame
        warning = False

        # Output the pressure profile config
        save_profile(
            frame,
            customProfile,
            False,
            warning
        )


def delete_profile(
    selectProfile
):
    """
    Variables
    ---------------------------------------------------------------------
    selectProfile           = <class> CTkComboBox object

    Description
    ---------------------------------------------------------------------
    Deletes the {selectProfile} from ~/config/profiles/.
    """

    global config

    # Check if 'Manual' profile is selected
    if config['settings']['profile'].upper().strip() == 'MANUAL':
        error(
            '[Manual] profile cannot be deleted.'
        )
    else:

        # Check if presure profile config exists
        try:
            if '.'.join([config['settings']['profile'], 'json']) in os.listdir(
                os.path.join(
                    config['session']['configLoc'],
                    'profiles'
                )
            ):

                # Create confirmation frame
                confirm = create_toplevel_frame(
                    master=root,
                    title='Confirmation',
                    width=342,
                    height=129,
                    numCols=4,
                    numRows=4,
                    fullscreen=False
                )

                # Define confirmation message
                message = (
                    'Are you sure you want to delete [%s]?' % (
                        config['settings']['profile']
                    )
                )

                # Declare confirmation frame components
                labelConfirm = customtkinter.CTkLabel(
                    confirm,
                    text=message
                )
                buttonNo = customtkinter.CTkButton(
                    confirm,
                    height=config['format']['buttonHeight'],
                    width=config['format']['buttonWidth'],
                    corner_radius=config['format']['buttonHeight'],
                    text='No',
                    command=lambda: back(confirm)
                )
                buttonYes = customtkinter.CTkButton(
                    confirm,
                    height=config['format']['buttonHeight'],
                    width=config['format']['buttonWidth'],
                    corner_radius=config['format']['buttonHeight'],
                    text='Yes',
                    command=lambda: delete_callback(
                        confirm,
                        selectProfile
                    )
                )

                # Pack confirmation frame components
                labelConfirm.grid(
                    column=0,
                    row=0,
                    columnspan=3,
                    rowspan=2,
                    padx=config['format']['padX'],
                    pady=config['format']['padY'],
                    sticky=tk.N+tk.S+tk.E+tk.W
                )
                buttonNo.grid(
                    column=0,
                    row=2,
                    columnspan=1,
                    rowspan=1,
                    padx=config['format']['padX'],
                    pady=config['format']['padY'],
                    sticky=tk.N+tk.S+tk.W
                )
                buttonYes.grid(
                    column=2,
                    row=2,
                    columnspan=1,
                    rowspan=1,
                    padx=config['format']['padX'],
                    pady=config['format']['padY'],
                    sticky=tk.N+tk.S+tk.E
                )

            else:
                error(
                    '%s does not exist. Refresh the Settings.' % (
                        config['settings']['profile']
                    )
                )

        except FileNotFoundError:
            print(
                'ERROR: %s does not exist.' % (
                    os.path.join(
                        config['session']['configLoc'],
                        'profiles'
                    )
                )
            )
            sys.exit()


def save_profile(
    frame,
    customProfile,
    inputWarning,
    warningFrame
):
    """
    Variables
    ---------------------------------------------------------------------
    frame                   = <class> CTkFrame object to close
    customProfile           = <dict> Dictionary object of the espresso
                                profile settings
    inputWarning            = <bool> Parameter to close the warning frame
    warningFrame            = <class> Additional CTKFrame object to close

    Description
    ---------------------------------------------------------------------
    Saves the espresso profile settings from {customProfile} to
    ~/config/profiles/.
    """

    # Close warning frame
    if inputWarning:
        warningFrame.destroy()

    # Write pressure profile config
    try:
        utils.write_config(
            configLoc=os.path.join(
                    config['session']['configLoc'],
                    'profiles',
                    '.'.join([
                        customProfile['settings']['profileName'],
                        'json'
                    ])
                ),
            config=customProfile
        )
    except FileNotFoundError as e:
        print(e)
        sys.exit()

    # Close the top-level frame
    frame.destroy()


def assign_profile(
    profile
):
    """
    Variables
    ---------------------------------------------------------------------
    profile                     = <dict> Dictionary object containing
                                    the pressure profile settings

    Description
    ---------------------------------------------------------------------
    Creates a pressure profile config in
    ~/config/profiles and sets
    config['settings']['profile'] = <profile>['profileName'].
    """

    global config

    # Write pressure profile config
    try:
        utils.write_config(
            configLoc=os.path.join(
                config['session']['configLoc'],
                'profiles',
                '.'.join([
                    profile['settings']['profileName'],
                    'json'
                ])
            ),
            config=profile
        )
    except FileNotFoundError as e:
        print(e)
        sys.exit()

    # Update config with new profile setting
    config['settings']['profile'] = profile['settings']['profileName']

    # Write config
    try:
        utils.write_config(
            configLoc=os.path.join(
                config['session']['configLoc'],
                'config.json'
            ),
            config=config
        )
    except FileNotFoundError as e:
        print(e)
        sys.exit()


def refresh_settings(
    selectProfile
):
    """
    Variables
    ---------------------------------------------------------------------
    selectProfile           = <class> CTkComboBox object

    Description
    ---------------------------------------------------------------------
    Refreshes the {selectProfile} combobox object with the latest
    pressure profile configs from ~/config/profiles/.
    """

    # Refresh list of pressure profiles
    if os.path.isdir(
        os.path.join(
            config['session']['configLoc'],
            'profiles'
        )
    ):
        profileLst = sorted(
            [
                item.split('.')[0] for item in os.listdir(
                    os.path.join(
                        config['session']['configLoc'],
                        'profiles'
                    )
                ) if (
                    (item.split('.')[0].upper().strip() != 'DTYPES') and
                    (item.split('.')[1].upper() == 'JSON')
                )
            ]
        )

    # Update the drop-down menu selection
    selectProfile.configure(values=[])
    selectProfile.configure(
        values=[*profileLst]
    )


def idle():
    """
    Variables
    ---------------------------------------------------------------------

    Description
    ---------------------------------------------------------------------
    Initiates idling.
    """

    global tkTempValue, tkPresValue

    if idling:

        # Read sensor values
        tkTempValue.set(tSensor.read_temp(config))
        tkPresValue.set(pSensor.read_pressure(config))

        # Continue idling
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
    """
    Variables
    ---------------------------------------------------------------------
    labelCounter            = <class> CTkLabel object
    buttonStart             = <class> CTkButton object
    buttonStop              = <class> CTkButton object
    buttonReset             = <class> CTkButton object
    buttonPlot              = <class> CTkButton object
    buttonSave              = <class> CTkButton object
    buttonSettings          = <class> CTkButton object
    buttonBack              = <class> CTkButton object

    Description
    ---------------------------------------------------------------------
    Initiates the brew timer and updates the state of {labelCounter},
    {buttonStart}, {buttonStop}, {buttonReset}, {buttonPlot},
    {buttonSave}, {buttonSettings}, and {buttonBack}.
    """

    global idling, running, flashing, counter, temperatureLst, pressureLst
    global tkCounter, tkTempValue, tkPresValue

    # Configure application state
    idling = False
    running = True
    flashing = False

    if not config['session']['dev']:
        GPIO.output(
            config['extraction']['pin'],
            GPIO.HIGH
        )

    # Update application omponents
    labelCounter.configure(text_color=theme['CTkLabel']['text_color'])
    buttonStart.configure(state='disabled')
    buttonStop.configure(state='normal')
    buttonReset.configure(state='normal')
    buttonPlot.configure(state='disabled')
    buttonSave.configure(state='disabled')
    buttonSettings.configure(state='disabled')
    buttonBack.configure(state='disabled')

    # Read pressure profile config
    profile = read_profile(
        profileName=config['settings']['profile']
    )

    if config['settings']['profile'].upper().strip() == 'MANUAL':

        # Allow manual control of timer
        count(
            dt.datetime.now(),
            profile,
            True,
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
        # Disable stop button
        buttonStop.configure(state='disabled')

        # Enforce program control of timer
        count(
            dt.datetime.now(),
            profile,
            False,
            labelCounter,
            buttonStart,
            buttonStop,
            buttonReset,
            buttonPlot,
            buttonSave,
            buttonSettings,
            buttonBack
        )


def count(
    countStart,
    profile,
    manual,
    labelCounter,
    buttonStart,
    buttonStop,
    buttonReset,
    buttonPlot,
    buttonSave,
    buttonSettings,
    buttonBack
):
    """
    Variables
    ---------------------------------------------------------------------
    countStart              = <class> Datetime value to calculate
                                the delay interval
    profile                 = <dict> Dictionary object containing the
                                profile settings.
    manual                  = <bool> Determines the stopping logic
    labelCounter            = <class> CTkLabel object
    buttonStart             = <class> CTkButton object
    buttonStop              = <class> CTkButton object
    buttonReset             = <class> CTkButton object
    buttonPlot              = <class> CTkButton object
    buttonSave              = <class> CTkButton object
    buttonSettings          = <class> CTkButton object
    buttonBack              = <class> CTkButton object

    Description
    ---------------------------------------------------------------------
    Increments the timer based on (100 - (start time - process time))
    and ends the count based on the pressure profile config.
    """

    global running, counter, temperatureLst, pressureLst
    global tkCounter, tkTempValue, tkPresValue

    if running:

        # Append sensor values
        temperatureLst.append(tSensor.read_temp(config))
        pressureLst.append(pSensor.read_pressure(config))

        # Update label text
        tkCounter.set(float(round(counter / 10, 1)))
        tkTempValue.set(temperatureLst[counter])
        tkPresValue.set(pressureLst[counter])

        # Increment counter
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
                    profile,
                    True,
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
        else:
            if (
                round(counter / 10, 1) >
                max(profile['settings']['timeLst'])
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
                        profile,
                        False,
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
    """
    Variables
    ---------------------------------------------------------------------
    labelCounter            = <class> CTkLabel object
    buttonStart             = <class> CTkButton object
    buttonStop              = <class> CTkButton object
    buttonReset             = <class> CTkButton object
    buttonPlot              = <class> CTkButton object
    buttonSave              = <class> CTkButton object
    buttonSettings          = <class> CTkButton object
    buttonBack              = <class> CTkButton object

    Description
    ---------------------------------------------------------------------
    Ends the brew timer and updates the state of {labelCounter},
    {buttonStart}, {buttonStop}, {buttonReset}, {buttonPlot},
    {buttonSave}, {buttonSettings}, and {buttonBack}.
    """

    global idling, running, flashing

    # Configure application state
    idling = False
    running = False
    flashing = True

    if not config['session']['dev']:
        GPIO.output(
            config['extraction']['pin'],
            GPIO.LOW
        )

    # Update application omponents
    buttonStart.configure(state='normal')
    buttonStop.configure(state='disabled')
    buttonReset.configure(state='normal')
    buttonPlot.configure(state='normal')
    buttonSave.configure(state='normal')
    buttonSettings.configure(state='disabled')
    buttonBack.configure(state='disabled')

    # Trigger flashing
    flash(
        labelCounter,
        dt.datetime.now()
    )


def flash(
    labelCounter,
    countStart
):
    """
    Variables
    ---------------------------------------------------------------------
    labelCounter            = <class> CTkLabel object
    countStart              = <class> Datetime value to calculate
                                the delay interval

    Description
    ---------------------------------------------------------------------
    Initiates the flashing animation.
    """

    if flashing:

        # Retrive text color tupple
        currentColor = labelCounter.cget('text_color')

        if labelCounter.cget('text_color') == currentColor[0]:
            labelCounter.configure(
                text_color=(currentColor[1], currentColor[0])
            )
        else:
            labelCounter.configure(
                text_color=(currentColor[1], currentColor[0])
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
    """
    Variables
    ---------------------------------------------------------------------
    labelCounter            = <class> CTkLabel object
    buttonStart             = <class> CTkButton object
    buttonStop              = <class> CTkButton object
    buttonReset             = <class> CTkButton object
    buttonPlot              = <class> CTkButton object
    buttonSave              = <class> CTkButton object
    buttonSettings          = <class> CTkButton object
    buttonBack              = <class> CTkButton object

    Description
    ---------------------------------------------------------------------
    Ends the brew timer and re-sets the state of {labelCounter},
    {buttonStart}, {buttonStop}, {buttonReset}, {buttonPlot},
    {buttonSave}, {buttonSettings}, and {buttonBack}.
    """

    global idling, running, flashing, counter, temperatureLst, pressureLst
    global tkCounter, tkTempValue, tkPresValue

    # Configure application state
    idling = True
    running = False
    flashing = False
    counter = 0
    temperatureLst = []
    pressureLst = []

    # Update application components
    tkCounter.set(float(round(counter / 10, 1)))
    tkTempValue.set(tSensor.read_temp(config))
    tkPresValue.set(pSensor.read_pressure(config))

    labelCounter.configure(text_color=theme['CTkLabel']['text_color'])
    buttonStart.configure(state='normal')
    buttonStop.configure(state='disabled')
    buttonReset.configure(state='disabled')
    buttonPlot.configure(state='disabled')
    buttonSave.configure(state='disabled')
    buttonSettings.configure(state='normal')
    buttonBack.configure(state='normal')

    # Trigger idling
    idle()


def calculate_profile_quartile(
    customProfile,
    timeLst
):
    """
    Variables
    ---------------------------------------------------------------------
    customProfile               = <dict> Dictionary object containing
                                    the parameters for a custom
                                    pressure profile config
    timeLst                     = <list> List object containing the
                                    time-series for the espresso
                                    extraction

    Description
    ---------------------------------------------------------------------
    Calculates the itervals for the configurable nodes based on the
    {timeLst}.
    """

    # Create pre-infusion profile
    pressureProfileLst = []

    if customProfile['settings']['infusionDuration'] == 0:
        profileMin = 0
    else:
        profileMin = int(
            customProfile['settings']['infusionDuration'] + 1
        )
        pressureProfileLst = [
            int(
                customProfile['settings']['infusionPressure']
            )
        ] * customProfile['settings']['infusionDuration'] * 10

        # Calculate Slope
        pressureProfileLst = calculate_slope(
            customProfile,
            pressureProfileLst,
            customProfile['settings']['infusionPressure'],
            customProfile['settings']['p0'],
            customProfile['settings']['infusionDuration'],
            profileMin
        )

    profileRange = list(
        np.arange(
            profileMin,
            float(
                customProfile['settings']['extractionDuration']
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

    # Calculate slope
    pressureProfileLst = calculate_slope(
        customProfile,
        pressureProfileLst,
        customProfile['settings']['p0'],
        customProfile['settings']['p1'],
        q0,
        q1
    )
    pressureProfileLst = calculate_slope(
        customProfile,
        pressureProfileLst,
        customProfile['settings']['p1'],
        customProfile['settings']['p2'],
        q1,
        q2
    )
    pressureProfileLst = calculate_slope(
        customProfile,
        pressureProfileLst,
        customProfile['settings']['p2'],
        customProfile['settings']['p3'],
        q2,
        q3
    )
    pressureProfileLst = calculate_slope(
        customProfile,
        pressureProfileLst,
        customProfile['settings']['p3'],
        customProfile['settings']['p4'],
        q3,
        q4
    )

    # Adjust final profile
    # Issue if three quartiles all have the same pressure
    pressureProfileLst.append(customProfile['settings']['p4'])

    if len(pressureProfileLst) != len(timeLst):
        pressureProfileLst += [
            customProfile['settings']['p4']
        ] * int(
            len(timeLst) - len(pressureProfileLst)
        )

    # Assign time values for scatter plot
    if customProfile['settings']['infusionDuration'] == 0:
        scatterXLst = [
            q0,
            q1,
            q2,
            q3,
            q4
        ]
    else:
        scatterXLst = [
            0,
            customProfile['settings']['infusionDuration'],
            q0,
            q1,
            q2,
            q3,
            q4
        ]

    # Return profile and quartile for scatter plot
    return pressureProfileLst, scatterXLst


def calculate_slope(
    customProfile,
    pressureProfileLst,
    pStart,
    pEnd,
    tStart,
    tEnd
):
    """
    Variables
    ---------------------------------------------------------------------
    customProfile               = <dict> Dictionary object
                                    containing the parameters
                                    for a custom espresso
                                    extraction profile.
    pressureProfileLst                 = <list> List object of the espresso
                                    extraction profile pressure values
    pStart                      = <int> Starting pressure value.
    pEnd                        = <int> Ending pressure value.
    tStart                      = <int> Starting temperature value.
    tEnd                        = <int> Ending temperature value.

    Description
    ---------------------------------------------------------------------
    Calculates the pressure and temperature values in-between the
    itervals for the pressure profile config.
    """

    # Calculate slope
    num = pEnd - pStart
    denom = int(
        (tEnd - tStart) * 10
    )
    m = float(num / denom)

    if pEnd == pStart:
        profNew = [pEnd] * denom
    else:
        profNew = [
            round(item, 1) for item in list(
                np.arange(
                    pStart,
                    pEnd,
                    m
                )
            )
        ]

    pressureProfileLst += profNew

    return pressureProfileLst


# Define application callback functions
def delete_callback(
    frame,
    selectProfile
):
    """
    Variables
    ---------------------------------------------------------------------
    frame                   = <class> CTkFrame object to close
    selectProfile           = <class> pressure profile config object

    Description
    ---------------------------------------------------------------------
    Deletes the {selectProfile} from ~/config/profiles/.
    """
    global config

    # Delete selected pressure profile config
    if os.path.isfile(
        os.path.join(
            config['session']['configLoc'],
            'profiles',
            '.'.join([
                config['settings']['profile'],
                'json'
            ])
        )
    ):
        os.remove(
            os.path.join(
                config['session']['configLoc'],
                'profiles',
                '.'.join([
                    config['settings']['profile'],
                    'json'
                ])
            )
        )

    # Reset pressure profile config
    assign_profile(
        profile={
            'settings': {
                'profileName': 'Manual',
                'extractionDuration': 0.0,
                'infusionDuration': 0,
                'infusionPressure': 0,
                'p0': 0,
                'p1': 0,
                'p2': 0,
                'p3': 0,
                'p4': 0,
                'timeLst': [],
                'pressureProfileLst': []
            }
        }
    )
    tkProfile.set(config['settings']['profile'])

    # Refresh pressure profile dropdown selection
    refresh_settings(selectProfile)

    # Close the top-level frame
    frame.destroy()


def scale_callback(
    value,
    selectSetPoint,
    setPointLst
):
    """
    Variables
    ---------------------------------------------------------------------
    value                   = <str> Temperature scale value.
    selectSetPoint          = <class> CTkOptionMenu object
    setPointLst             = <list> List object of valid set-point
                                values.

    Description
    ---------------------------------------------------------------------
    Updates the available temperature set-point values within the
    settings form.
    """

    global config, tkSetPoint

    # Assign Temperature range based on scale {value}
    if config['settings']['scaleLabel'].split(' ')[1] != value.split(' ')[1]:
        if value.split(' ')[1] == '[F]':

            # Convert from celsius to fahrenheit
            setPointLst = list(
                np.arange(
                    200,
                    220,
                    1
                )
            )
            config['tPID']['setPoint'] = float(
                round(
                    (
                        tkSetPoint.get() * 9 / 5
                    ) + 32,
                    0
                )
            )
            config['tPID']['deadZoneRange'] = float(
                (
                    config['tPID']['deadZoneRange'] * 9 / 5
                ) + 32
            )

            # Limit upper and lower bounds
            if config['tPID']['setPoint'] < 200:
                config['tPID']['setPoint'] = 200
            elif config['tPID']['setPoint'] > 220:
                config['tPID']['setPoint'] = 220
            else:
                pass

        else:

            # Convert from fahrenheit to celsius
            setPointLst = [
                round(item, 1) for item in list(
                    np.arange(
                        93,
                        104.5,
                        0.5
                    )
                )
            ]
            config['tPID']['setPoint'] = float(
                round(
                    (
                        (
                            tkSetPoint.get() - 32
                        ) * 5 / 9
                    ) * 2
                ) / 2
            )
            config['tPID']['deadZoneRange'] = float(
                round(
                    (
                        (
                            config['tPID']['deadZoneRange'] - 32
                        ) * 5 / 9
                    ) * 2
                ) / 2
            )

            # Limit upper and lower bounds
            if config['tPID']['setPoint'] < 93:
                config['tPID']['setPoint'] = 93
            elif config['tPID']['setPoint'] > 104.5:
                config['tPID']['setPoint'] = 104.5
            else:
                pass

        # Update settings
        config['settings']['scaleLabel'] = str(value)
        config['settings']['scale'] = re.sub(
            r'\W+',
            '',
            str(value.split(' ')[1])
        )
        try:
            utils.write_config(
                configLoc=os.path.join(
                    config['session']['configLoc'],
                    'config.json'
                ),
                config=config
            )
        except FileNotFoundError as e:
            print(e)
            sys.exit()

        # Update tkinter variables
        tkSetPoint.set(config['tPID']['setPoint'])

        # Update the drop-down menu selection
        selectSetPoint.configure(values=[])
        selectSetPoint.configure(
            values=[*[str(setPoint) for setPoint in setPointLst]]
        )

    else:
        pass


def setpoint_callback(
    value
):
    """
    Variables
    ---------------------------------------------------------------------
    value                   = <int> Temperature set-point value.

    Description
    ---------------------------------------------------------------------
    Updates the config with the selected set-point {value}.
    """

    global config

    # Update settings
    config['tPID']['setPoint'] = float(value)
    try:
        utils.write_config(
            configLoc=os.path.join(
                config['session']['configLoc'],
                'config.json'
            ),
            config=config
        )
    except FileNotFoundError as e:
        print(e)
        sys.exit()


def profile_callback(
    value
):
    """
    Variables
    ---------------------------------------------------------------------
    value                   = <str> pressure profile config value.

    Description
    ---------------------------------------------------------------------
    Updates the config with the selected profile {value}.
    """

    global config

    # Update settings
    config['settings']['profile'] = str(value).strip()
    try:
        utils.write_config(
            configLoc=os.path.join(
                config['session']['configLoc'],
                'config.json'
            ),
            config=config
        )
    except FileNotFoundError as e:
        print(e)
        sys.exit()


def flush_callback(
    value
):
    """
    Variables
    ---------------------------------------------------------------------
    value                   = <int> Flush duration value.

    Description
    ---------------------------------------------------------------------
    Updates the config with the selected flush {value}.
    """

    global config

    # Update settings
    config['settings']['flush'] = int(value)
    try:
        utils.write_config(
            configLoc=os.path.join(
                config['session']['configLoc'],
                'config.json'
            ),
            config=config
        )
    except FileNotFoundError as e:
        print(e)
        sys.exit()


def add_profile_callback(
    timeLst,
    pressureProfileLst
):
    """
    Variables
    ---------------------------------------------------------------------
    timeLst                     = <list> List object of the espresso
                                    extraction time-intervals
    pressureProfileLst                 = <list> List object of the espresso
                                    extraction profile pressure values

    Description
    ---------------------------------------------------------------------
    Writes the pressure profile config to ~/config/profiles/.
    """

    # Create pressure profile config dictionary
    if os.path.isdir(
        os.path.join(
            config['session']['configLoc'],
            'profiles'
        )
    ):
        profileLst = sorted(
            [
                item.split('.')[0] for item in os.listdir(
                    os.path.join(
                        config['session']['configLoc'],
                        'profiles'
                    )
                ) if (
                    (item.split('.')[0].upper().strip() != 'DTYPES') and
                    (item.split('.')[1].upper() == 'JSON')
                )
            ]
        )
        userProfiles = [
            item for item in profileLst if 'USER_' in item.upper()
        ]
        if userProfiles == []:
            profileNum = 1
        else:
            profileNum = int(
                max(
                    int(item.split('_')[1]) for item in userProfiles
                ) + 1
            )

    userProfile = {
        'settings': {
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
            'pressureProfileLst': pressureProfileLst
        }
    }

    # Create profile name frame
    profileName = create_toplevel_frame(
        master=root,
        title='Input Profile Name',
        width=342,
        height=129,
        numCols=4,
        numRows=4,
        fullscreen=False
    )

    tkUserProfileName = tk.StringVar()
    tkUserProfileName.set('User_'+str(profileNum))

    # Declare profile name frame components
    labelProfileName = customtkinter.CTkLabel(
        profileName,
        text='Profile Name:'
    )
    valueProfileName = customtkinter.CTkEntry(
        profileName,
        textvariable=tkUserProfileName
    )
    buttonBack = customtkinter.CTkButton(
        profileName,
        height=config['format']['buttonHeight'],
        width=config['format']['buttonWidth'],
        corner_radius=config['format']['buttonHeight'],
        text='Back',
        command=lambda: back(profileName)
    )
    buttonAddProfile = customtkinter.CTkButton(
        profileName,
        height=config['format']['buttonHeight'],
        width=config['format']['buttonWidth'],
        corner_radius=config['format']['buttonHeight'],
        text='Okay',
        command=lambda: check_profile(
            profileName,
            userProfile,
            tkUserProfileName
        )
    )

    # Pack profile name frame components
    labelProfileName.grid(
        column=0,
        row=0,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    valueProfileName.grid(
        column=0,
        row=1,
        columnspan=3,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonBack.grid(
        column=0,
        row=2,
        columnspan=2,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    buttonAddProfile.grid(
        column=2,
        row=2,
        columnspan=2,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )


def plot_profile_callback(
    value,
    tkProfParams,
    key,
    customProfile,
    canvasProf,
    p1,
    p2,
    profFig
):
    """
    Variables
    ---------------------------------------------------------------------
    value                       = <str/int/float> Value to assign to the
                                    pressure profile {key}
    tkProfParams                = <class> Tkinter StringVar object
    key                         = <dict> Dictionary object key
    customProfile               = <dict> Dictionary object containing the
                                    custom pressure profile settings
    canvasProf                  = <class> Tkinter canvas object
    p1                          = <class> Plot axis, temperature
    p2                          = <class> Secondary plot axis, pressure
    profFig                     = <class> matplotlib.pyplot.figure object

    Description
    ---------------------------------------------------------------------
    Re-plots the custom profile based on the slider selections.
    """

    # Update profile dictionary value
    if key == 'profileName':
        customProfile['settings'][key] = value
    elif key == 'extractionDuration':
        customProfile['settings'][key] = float(value)
    else:
        customProfile['settings'][key] = int(value)

    # Create time series list
    timeLst = list(
        np.arange(
            0,
            float(customProfile['settings']['extractionDuration'] + 1),
            0.1
        )
    )
    timeLst = [
        round(item, 1)
        for item in timeLst
    ]
    customProfile['settings']['timeLst'] = timeLst

    # Return pressure profile and quartiles
    pressureProfileLst, scatterXLst = calculate_profile_quartile(
        customProfile,
        timeLst
    )
    customProfile['settings']['pressureProfileLst'] = pressureProfileLst

    # Assign pressure values for scatter
    if customProfile['settings']['infusionDuration'] == 0:
        scatterYLst = [
            customProfile['settings']['p0'],
            customProfile['settings']['p1'],
            customProfile['settings']['p2'],
            customProfile['settings']['p3'],
            customProfile['settings']['p4']
        ]
    else:
        scatterYLst = [
            customProfile['settings']['infusionPressure'],
            customProfile['settings']['infusionPressure'],
            customProfile['settings']['p0'],
            customProfile['settings']['p1'],
            customProfile['settings']['p2'],
            customProfile['settings']['p3'],
            customProfile['settings']['p4']
        ]

    # Update parameter label
    tkProfParams.set(
        'Params: ' +
        str(customProfile['settings']['extractionDuration']) +
        ' [Sec.], Pre-Inf. ' +
        str(customProfile['settings']['infusionDuration']) +
        ' [Sec.] at ' +
        str(customProfile['settings']['infusionPressure']) +
        ' [Bars], {P0:' +
        str(customProfile['settings']['p0']) +
        ', P1:' +
        str(customProfile['settings']['p1']) +
        ', P2:' +
        str(customProfile['settings']['p2']) +
        ', P3:' +
        str(customProfile['settings']['p3']) +
        ', P4:' +
        str(customProfile['settings']['p4']) + '}'
    )

    # Clear, format and plot temperature values
    p1.clear()
    p1.set_ylabel(
        'Pressure [Bars]',
        color=config['format']['red']
    )
    p1.set_xlim(
        round(min(timeLst), 1),
        round(max(timeLst), 1)
    )
    p1.set_ylim(
        0,
        12
    )
    p1.tick_params(
        axis='y',
        labelcolor=config['format']['red'],
        labelsize=config['format']['labelSize'] * 0.5,
        length=0,
        pad=10
    )
    p1.tick_params(
        axis='x',
        labelcolor=config['format']['color1'],
        labelsize=config['format']['labelSize'] * 0.5,
        length=0,
        pad=5
    )
    p1.plot(
        timeLst,
        pressureProfileLst,
        linewidth=2,
        color=config['format']['red']
    )

    p2.clear()
    p2.set_ylim(
        0,
        12
    )
    p2.scatter(
        scatterXLst,
        scatterYLst,
        c=config['format']['red'],
        marker='o'
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
    profFig.subplots_adjust(top=0.95, bottom=0.10)

    # Update the canvas
    canvasProf.draw()


# Define application frame functions
def create_toplevel_frame(
    master,
    title,
    width,
    height,
    numCols,
    numRows,
    fullscreen
):
    """
    Variables
    ---------------------------------------------------------------------
    master                      = <class> CTkToplevel object
    title                       = <str> Title of the new top-level frame
    width                       = <int> Width in pixels of the frame
    height                      = <int> Height in pixels of the frame

    Description
    ---------------------------------------------------------------------
    Creates and returns a new CTkToplevel object.
    """

    # Declare frame
    frame = customtkinter.CTkToplevel(
        master=master
    )
    frame.title(title)

    # Assign environment settings
    if not config['session']['dev']:
        frame.configure(cursor='none')

        if fullscreen:
            frame.attributes('-fullscreen', True)

    # Configure frame
    for c in range(0, int(numCols-1)):
        frame.columnconfigure(
            c,
            minsize=90,
            weight=1
        )
    for r in range(0, int(numRows-1)):
        frame.rowconfigure(
            r,
            minsize=30,
            weight=1
        )

    # Size & position frame
    frame.geometry(
        "{}x{}+{}+{}".format(
            width,
            height,
            int((frame.winfo_screenwidth()/2) - (width/2)),
            int((frame.winfo_screenheight()/2) - (height/2))
        )
    )
    return frame


def create_dashboard():
    """
    Variables
    ---------------------------------------------------------------------

    Description
    ---------------------------------------------------------------------
    Initializes the dashboard frame.
    """

    # Create dashboard frame
    dashboard = create_toplevel_frame(
        master=root,
        title='Dashboard',
        width=config['format']['width'],
        height=config['format']['height'],
        numCols=8,
        numRows=12,
        fullscreen=True
    )

    # Declare eashboard frame components
    buttonBack = customtkinter.CTkButton(
        dashboard,
        height=config['format']['buttonHeight'],
        width=config['format']['buttonWidth'],
        corner_radius=config['format']['buttonHeight'],
        text='Back',
        command=lambda: back(dashboard)
    )
    buttonClose = customtkinter.CTkButton(
        dashboard,
        height=config['format']['buttonHeight'],
        width=config['format']['buttonWidth'],
        corner_radius=config['format']['buttonHeight'],
        text='Close',
        command=close
    )
    buttonFlush = customtkinter.CTkButton(
        dashboard,
        height=config['format']['buttonHeight'],
        width=config['format']['buttonWidth'],
        corner_radius=config['format']['buttonHeight'],
        text='Flush',
        command=button_press,
        state='disabled'
    )
    buttonStart = customtkinter.CTkButton(
        dashboard,
        height=config['format']['buttonHeight']*2,
        width=config['format']['buttonWidth'],
        corner_radius=config['format']['buttonHeight']/2,
        text='Start',
        fg_color=config['format']['green'],
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
    buttonStop = customtkinter.CTkButton(
        dashboard,
        height=config['format']['buttonHeight']*2,
        width=config['format']['buttonWidth'],
        corner_radius=config['format']['buttonHeight']/2,
        text='Stop',
        fg_color=config['format']['red'],
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
    buttonSave = customtkinter.CTkButton(
        dashboard,
        height=config['format']['buttonHeight'],
        width=config['format']['buttonWidth'],
        corner_radius=config['format']['buttonHeight'],
        text='Save',
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
    buttonReset = customtkinter.CTkButton(
        dashboard,
        height=config['format']['buttonHeight'],
        width=config['format']['buttonWidth'],
        corner_radius=config['format']['buttonHeight'],
        text='Reset',
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
    buttonPlot = customtkinter.CTkButton(
        dashboard,
        height=config['format']['buttonHeight']*2,
        width=config['format']['buttonWidth'],
        corner_radius=config['format']['buttonHeight']/2,
        text='Plot',
        state='disabled',
        command=lambda: create_plot()
    )
    buttonSettings = customtkinter.CTkButton(
        dashboard,
        height=config['format']['buttonHeight']*2,
        width=config['format']['buttonWidth'],
        corner_radius=config['format']['buttonHeight']/2,
        text='Settings',
        command=create_settings
    )
    labelCounter = customtkinter.CTkLabel(
        dashboard,
        textvariable=tkCounter,
        font=(
            config['format']['font'],
            config['format']['counterSize'],
            'bold'
        )
    )
    labelTDesc = customtkinter.CTkLabel(
        dashboard,
        textvariable=tkScale,
        font=(
            config['format']['font'],
            config['format']['headerSize']
        )
    )
    valueTMetric = customtkinter.CTkLabel(
        dashboard,
        textvariable=tkTempValue,
        font=(
            config['format']['font'],
            config['format']['metricsSize'],
            'bold'
        ),
        text_color=config['format']['blue']
    )
    labelPDesc = customtkinter.CTkLabel(
        dashboard,
        text='Pressure [Bars]',
        font=(
            config['format']['font'],
            config['format']['headerSize']
        )
    )
    valuePMetric = customtkinter.CTkLabel(
        dashboard,
        textvariable=tkPresValue,
        font=(
            config['format']['font'],
            config['format']['metricsSize'],
            'bold'
        ),
        text_color=config['format']['red']
    )
    labelSet = customtkinter.CTkLabel(
        dashboard,
        text='Set-Point:'
    )
    valueSet = customtkinter.CTkLabel(
        dashboard,
        textvariable=tkSetPoint,
        font=(
            config['format']['font'],
            config['format']['labelSize'],
            'bold'
        ),
        text_color=config['format']['blue']
    )
    labelFlush = customtkinter.CTkLabel(
        dashboard,
        text='Flush [Sec.]:'
    )
    valueFlush = customtkinter.CTkLabel(
        dashboard,
        textvariable=tkFlush,
        font=(
            config['format']['font'],
            config['format']['labelSize'],
            'bold'
        )
    )
    labelProfile = customtkinter.CTkLabel(
        dashboard,
        text='Profile:'
    )
    valueProfile = customtkinter.CTkLabel(
        dashboard,
        textvariable=tkProfile,
        font=(
            config['format']['font'],
            config['format']['labelSize'],
            'bold'
        )
    )

    # Pack dashboard frame components
    buttonBack.grid(
        column=0,
        row=0,
        columnspan=2,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    buttonClose.grid(
        column=5,
        row=0,
        columnspan=2,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    buttonFlush.grid(
        column=0,
        row=1,
        columnspan=2,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    buttonStart.grid(
        column=1,
        row=8,
        columnspan=1,
        rowspan=2,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonStop.grid(
        column=2,
        row=8,
        columnspan=1,
        rowspan=2,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonSave.grid(
        column=3,
        row=8,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonReset.grid(
        column=3,
        row=9,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonPlot.grid(
        column=4,
        row=8,
        columnspan=1,
        rowspan=2,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonSettings.grid(
        column=5,
        row=8,
        columnspan=1,
        rowspan=2,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    labelCounter.grid(
        column=0,
        row=2,
        columnspan=4,
        rowspan=5,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    labelTDesc.grid(
        column=3,
        row=2,
        columnspan=2,
        rowspan=2,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    valueTMetric.grid(
        column=5,
        row=2,
        columnspan=2,
        rowspan=2,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    labelPDesc.grid(
        column=3,
        row=5,
        columnspan=2,
        rowspan=2,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    valuePMetric.grid(
        column=5,
        row=5,
        columnspan=2,
        rowspan=2,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    labelSet.grid(
        column=0,
        row=10,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    valueSet.grid(
        column=1,
        row=10,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    labelFlush.grid(
        column=2,
        row=10,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    valueFlush.grid(
        column=3,
        row=10,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    labelProfile.grid(
        column=4,
        row=10,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    valueProfile.grid(
        column=5,
        row=10,
        columnspan=2,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.W
    )


def create_plot():
    """
    Variables
    ---------------------------------------------------------------------

    Description
    ---------------------------------------------------------------------
    Plots the espresso extraction data.
    """

    global config, temperatureLst, pressureLst

    # Create plot frame
    plot = create_toplevel_frame(
        master=root,
        title='Plot',
        width=config['format']['width'],
        height=config['format']['height'],
        numCols=8,
        numRows=12,
        fullscreen=True
    )

    # Create time series list
    timeLst = [
        round(item / 10, 1) for item in list(
            range(
                0,
                len(temperatureLst)
            )
        )
    ]

    # Read pressure profile config
    profile = read_profile(
        profileName=config['settings']['profile']
    )

    # Calculate espresso extraction statistics
    if config['settings']['profile'].upper().strip() == 'MANUAL':
        correl = 'NA'
        plotProfile = False

    else:
        correl = float(
            round(
                pearsonr(
                    pressureLst,
                    profile['settings']['pressureProfileLst']
                )[0] * 100, 2
            )
        )
        plotProfile = True

    # Create plot figure
    fig = plt.figure()
    fig.patch.set_facecolor(config['format']['color4'])

    x1 = fig.add_subplot(1, 1, 1)
    x1.set_facecolor(config['format']['color3'])
    x2 = x1.twinx()

    for axes in [x1, x2]:
        for border in [
            'top',
            'bottom',
            'right',
            'left'
        ]:
            axes.spines[border].set_visible(False)

    # Get DPI and assign dimmensions to figure
    DPI = float(fig.get_dpi())
    fig.set_size_inches(780 / DPI, 280 / DPI)

    # Clear, format and plot temperature values
    x1.clear()
    x1.set_ylabel(
        'Temperature ' + config['settings']['scaleLabel'].split(' ')[1],
        color=config['format']['blue']
    )
    x1.set_xlim(
        min(timeLst),
        max(timeLst)
    )
    x1.set_ylim(
        int(round((min(temperatureLst)-15))),
        int(round((max(temperatureLst)+15)))
    )
    x1.tick_params(
        axis='y',
        labelcolor=config['format']['blue'],
        labelsize=config['format']['labelSize'] * 0.5,
        length=0,
        pad=10
    )
    x1.tick_params(
        axis='x',
        labelcolor=config['format']['color1'],
        labelsize=config['format']['labelSize'] * 0.5,
        length=0,
        pad=10
    )
    x1.plot(
        timeLst,
        temperatureLst,
        linewidth=2,
        color=config['format']['blue']
    )
    x1.plot(
        timeLst,
        [config['tPID']['setPoint']] * len(timeLst),
        linewidth=2,
        color=config['format']['blue'],
        linestyle='--',
        alpha=0.4
    )
    x1.fill_between(
        timeLst,
        temperatureLst,
        0,
        linewidth=0,
        color=config['format']['blue'],
        alpha=0.4
    )

    # Clear, format and plot temperature values
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
        color=config['format']['red']
    )
    x2.tick_params(
        axis='y',
        labelcolor=config['format']['red'],
        labelsize=config['format']['labelSize'] * 0.5,
        length=0,
        pad=10
    )
    x2.tick_params(
        axis='x',
        labelcolor=config['format']['color1'],
        labelsize=config['format']['labelSize'] * 0.5,
        length=0,
        pad=10
    )
    x2.plot(
        timeLst,
        pressureLst,
        linewidth=2,
        color=config['format']['red']
    )

    if plotProfile:
        x2.plot(
            timeLst,
            profile['settings']['pressureProfileLst'],
            linewidth=2,
            color=config['format']['red'],
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
    fig.subplots_adjust(top=0.90, bottom=0.15)

    # Declare plot frame components
    buttonBack = customtkinter.CTkButton(
        plot,
        height=config['format']['buttonHeight'],
        width=config['format']['buttonWidth'],
        corner_radius=config['format']['buttonHeight'],
        text='Back',
        command=lambda: back(plot)
    )
    buttonClose = customtkinter.CTkButton(
        plot,
        height=config['format']['buttonHeight'],
        width=config['format']['buttonWidth'],
        corner_radius=config['format']['buttonHeight'],
        text='Close',
        command=close
    )
    buttonAddProfile = customtkinter.CTkButton(
        plot,
        height=config['format']['buttonHeight'],
        width=config['format']['buttonWidth'],
        corner_radius=config['format']['buttonHeight'],
        text='Add Profile',
        command=lambda: add_profile_callback(
            timeLst,
            pressureLst
        )
    )
    labelTitle = customtkinter.CTkLabel(
        plot,
        text='Espresso Extraction Performance',
        font=(
            config['format']['font'],
            config['format']['headerSize'],
            'bold'
        )
    )
    labelStats = customtkinter.CTkLabel(
        plot,
        text='Correl [%]:'
    )
    valueStats = customtkinter.CTkLabel(
        plot,
        text=str(correl),
        font=(
            config['format']['font'],
            config['format']['labelSize'],
            'bold'
        )
    )
    canvas = FigureCanvasTkAgg(
        fig,
        master=plot
    )
    canvasPlot = canvas.get_tk_widget()
    labelXAxis = customtkinter.CTkLabel(
        plot,
        text='Time [Sec.]'
    )
    labelDuration = customtkinter.CTkLabel(
        plot,
        text='Duration:'
    )
    valueDuration = customtkinter.CTkLabel(
        plot,
        text=str(max(timeLst))+' Sec.',
        font=(
            config['format']['font'],
            config['format']['labelSize'],
            'bold'
        )
    )
    labelProfile = customtkinter.CTkLabel(
        plot,
        text='Profile:'
    )
    valueProfile = customtkinter.CTkLabel(
        plot,
        textvariable=tkProfile,
        font=(
            config['format']['font'],
            config['format']['labelSize'],
            'bold'
        )
    )

    # Pack plot frame components
    buttonBack.grid(
        column=0,
        row=0,
        columnspan=2,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    buttonClose.grid(
        column=5,
        row=0,
        columnspan=2,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    buttonAddProfile.grid(
        column=6,
        row=10,
        columnspan=2,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    labelTitle.grid(
        column=1,
        row=0,
        columnspan=5,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.S+tk.E+tk.W
    )
    labelStats.grid(
        column=2,
        row=1,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    valueStats.grid(
        column=3,
        row=1,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    canvasPlot.grid(
        column=0,
        row=2,
        columnspan=7,
        rowspan=8,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.E+tk.W
    )
    labelXAxis.grid(
        column=2,
        row=9,
        columnspan=3,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.E+tk.W
    )
    labelDuration.grid(
        column=1,
        row=10,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    valueDuration.grid(
        column=2,
        row=10,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    labelProfile.grid(
        column=3,
        row=10,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    valueProfile.grid(
        column=4,
        row=10,
        columnspan=2,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.W
    )


def create_settings():
    """
    Variables
    ---------------------------------------------------------------------

    Description
    ---------------------------------------------------------------------
    Initializes the settings frame.
    """

    # Create settings frame
    settings = create_toplevel_frame(
        master=root,
        title='Settings',
        width=config['format']['width'],
        height=config['format']['height'],
        numCols=8,
        numRows=12,
        fullscreen=True
    )

    # Check for pressure profile configs
    if os.path.isdir(
        os.path.join(
            config['session']['configLoc'],
            'profiles'
        )
    ):
        profileLst = sorted(
            [
                item.split('.')[0] for item in os.listdir(
                    os.path.join(
                        config['session']['configLoc'],
                        'profiles'
                    )
                ) if (
                    (item.split('.')[0].upper().strip() != 'DTYPES') and
                    (item.split('.')[1].upper() == 'JSON')
                )
            ]
        )

    # Declare settings frame components
    buttonBack = customtkinter.CTkButton(
        settings,
        height=config['format']['buttonHeight'],
        width=config['format']['buttonWidth'],
        corner_radius=config['format']['buttonHeight'],
        text='Back',
        command=lambda: save_settings(
            settings
        )
    )
    buttonClose = customtkinter.CTkButton(
        settings,
        height=config['format']['buttonHeight'],
        width=config['format']['buttonWidth'],
        corner_radius=config['format']['buttonHeight'],
        text='Close',
        command=close
    )
    buttonDeleteProfile = customtkinter.CTkButton(
        settings,
        height=config['format']['buttonHeight'],
        width=config['format']['buttonWidth'],
        corner_radius=config['format']['buttonHeight'],
        text='Delete',
        command=lambda: delete_profile(
            selectProfile
        )
    )
    buttonUpdateProfile = customtkinter.CTkButton(
        settings,
        height=config['format']['buttonHeight'],
        width=config['format']['buttonWidth'],
        corner_radius=config['format']['buttonHeight'],
        text='Edit',
        command=lambda: create_profile(
            True
        )
    )
    buttonNewProfile = customtkinter.CTkButton(
        settings,
        height=config['format']['buttonHeight'],
        width=config['format']['buttonWidth'],
        corner_radius=config['format']['buttonHeight'],
        text='New',
        command=lambda: create_profile(
            False
        )
    )
    buttonRefresh = customtkinter.CTkButton(
        settings,
        height=config['format']['buttonHeight'],
        width=config['format']['buttonWidth'],
        corner_radius=config['format']['buttonHeight'],
        text='Refresh',
        command=lambda: refresh_settings(
            selectProfile
        )
    )
    labelTHead = customtkinter.CTkLabel(
        settings,
        textvariable=tkScale,
        font=(
            config['format']['font'],
            config['format']['labelSize'],
            'bold'
        )
    )
    labelOptnSetPoint = customtkinter.CTkLabel(
        settings,
        text='Set-Point:'
    )
    selectSetPoint = customtkinter.CTkOptionMenu(
        settings,
        variable=tkSetPoint,
        values=[*[str(setPoint) for setPoint in setPointLst]],
        button_color=config['format']['blue'],
        button_hover_color=config['format']['blue'],
        command=setpoint_callback
    )
    labelOptnScale = customtkinter.CTkLabel(
        settings,
        text='Scale:'
    )
    selectScale = customtkinter.CTkOptionMenu(
        settings,
        variable=tkScale,
        values=[*scaleLst],
        button_color=config['format']['blue'],
        button_hover_color=config['format']['blue'],
        command=lambda value=tkScale,
        selectSetPoint=selectSetPoint,
        setPointLst=setPointLst: scale_callback(
            value,
            selectSetPoint,
            setPointLst
        )
    )
    labelPHead = customtkinter.CTkLabel(
        settings,
        text='Pressure Profile',
        font=(
            config['format']['font'],
            config['format']['labelSize'],
            'bold'
        )
    )
    labelOptnProfile = customtkinter.CTkLabel(
        settings,
        text='Profile:'
    )
    selectProfile = customtkinter.CTkOptionMenu(
        settings,
        variable=tkProfile,
        values=[*profileLst],
        button_color=config['format']['blue'],
        button_hover_color=config['format']['blue'],
        command=profile_callback
    )
    labelFHead = customtkinter.CTkLabel(
        settings,
        text='Flush [Sec.]',
        font=(
            config['format']['font'],
            config['format']['labelSize'],
            'bold'
        )
    )
    selectFlush = customtkinter.CTkOptionMenu(
        settings,
        variable=tkFlush,
        values=[*[str(flush) for flush in flushLst]],
        button_color=config['format']['blue'],
        button_hover_color=config['format']['blue'],
        command=flush_callback
    )
    labelOptnFlush = customtkinter.CTkLabel(
        settings,
        text='Duration:'
    )

    # Pack settings frame components
    buttonBack.grid(
        column=0,
        row=0,
        columnspan=2,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    buttonClose.grid(
        column=5,
        row=0,
        columnspan=2,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    buttonDeleteProfile.grid(
        column=3,
        row=4,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    buttonUpdateProfile.grid(
        column=4,
        row=4,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    buttonNewProfile.grid(
        column=5,
        row=4,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    buttonRefresh.grid(
        column=0,
        row=10,
        columnspan=2,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    labelTHead.grid(
        column=1,
        row=1,
        columnspan=2,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    labelOptnScale.grid(
        column=2,
        row=1,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    selectScale.grid(
        column=3,
        row=1,
        columnspan=3,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    labelOptnSetPoint.grid(
        column=2,
        row=2,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    selectSetPoint.grid(
        column=3,
        row=2,
        columnspan=3,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    labelPHead.grid(
        column=1,
        row=3,
        columnspan=2,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    labelOptnProfile.grid(
        column=2,
        row=3,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    selectProfile.grid(
        column=3,
        row=3,
        columnspan=3,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    labelFHead.grid(
        column=1,
        row=5,
        columnspan=2,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    labelOptnFlush.grid(
        column=2,
        row=5,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    selectFlush.grid(
        column=3,
        row=5,
        columnspan=3,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )


def create_profile(
    update
):
    """
    Variables
    ---------------------------------------------------------------------
    update                      = <bool> Determines whether the profile
                                    is to be edited

    Description
    ---------------------------------------------------------------------
    Initializes the settings frame.
    """

    # Check if 'Manual' profile is selected
    if (
        (update) and
        (config['settings']['profile'].upper().strip() == 'MANUAL')
    ):
        error('[Manual] profile cannot be modified.')

    else:

        # Create profile frame
        profile = create_toplevel_frame(
            master=root,
            title='Pressure Profile',
            width=config['format']['width'],
            height=config['format']['height'],
            numCols=8,
            numRows=12,
            fullscreen=True
        )

        # Create pressure profile config
        if update:

            # Read pressure profile config
            customProfile = read_profile(
                profileName=config['settings']['profile']
            )

        # Create custom pressure profile config
        else:
            profileLst = sorted(
                [
                    item.split('.')[0] for item in os.listdir(
                        os.path.join(
                            config['session']['configLoc'],
                            'profiles'
                        )
                    ) if (
                        (item.split('.')[0].upper().strip() != 'DTYPES') and
                        (item.split('.')[1].upper() == 'JSON')
                    )
                ]
            )
            customProfiles = [
                item for item in profileLst if 'CUSTOM_' in item.upper()
            ]
            if customProfiles == []:
                profileNum = 1
            else:
                profileNum = int(
                    max(
                        int(item.split('_')[1]) for item in customProfiles
                    ) + 1
                )

            customProfile = {
                'settings': {
                    'profileName': 'Custom_'+str(profileNum),
                    'extractionDuration': 25.0,
                    'infusionDuration': 3,
                    'infusionPressure': 3,
                    'p0': 9,
                    'p1': 9,
                    'p2': 9,
                    'p3': 9,
                    'p4': 9,
                    'timeLst': [],
                    'pressureProfileLst': []
                }
            }

        # Store profile dictionary selections
        tkProfileName = tk.StringVar(root)
        tkProfileName.set(customProfile['settings']['profileName'])

        tkExtractionDur = tk.DoubleVar(root)
        tkExtractionDur.set(customProfile['settings']['extractionDuration'])

        tkInfusionDur = tk.IntVar(root)
        infusionDurationLst = list(range(0, 11))
        tkInfusionDur.set(customProfile['settings']['infusionDuration'])

        tkInfusionPres = tk.IntVar(root)
        infusionPressureLst = list(range(1, 6))
        tkInfusionPres.set(customProfile['settings']['infusionPressure'])

        tkP0 = tk.IntVar(root)
        tkP0.set(customProfile['settings']['p0'])

        tkP1 = tk.IntVar(root)
        tkP1.set(customProfile['settings']['p1'])

        tkP2 = tk.IntVar(root)
        tkP2.set(customProfile['settings']['p2'])

        tkP3 = tk.IntVar(root)
        tkP3.set(customProfile['settings']['p3'])

        tkP4 = tk.IntVar(root)
        tkP4.set(customProfile['settings']['p4'])

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

        # Create time series list
        timeLst = list(
            np.arange(
                0,
                float(customProfile['settings']['extractionDuration'] + 1),
                0.1
            )
        )
        timeLst = [
            round(item, 1) for item in timeLst
        ]
        customProfile['settings']['timeLst'] = timeLst

        # Return initial pressure profile and quartiles
        pressureProfileLst, scatterXLst = calculate_profile_quartile(
            customProfile,
            timeLst
        )
        customProfile['settings']['pressureProfileLst'] = pressureProfileLst

        # Assign pressure values for scatter
        if customProfile['settings']['infusionDuration'] == 0:
            scatterYLst = [
                customProfile['settings']['p0'],
                customProfile['settings']['p1'],
                customProfile['settings']['p2'],
                customProfile['settings']['p3'],
                customProfile['settings']['p4']
            ]
        else:
            scatterYLst = [
                customProfile['settings']['infusionPressure'],
                customProfile['settings']['infusionPressure'],
                customProfile['settings']['p0'],
                customProfile['settings']['p1'],
                customProfile['settings']['p2'],
                customProfile['settings']['p3'],
                customProfile['settings']['p4']
            ]

        # Create figure for plot
        profFig = plt.figure()
        profFig.patch.set_facecolor(config['format']['color4'])

        p1 = profFig.add_subplot(1, 1, 1)
        p1.set_facecolor(config['format']['color3'])
        p2 = p1.twinx()

        for axes in [p1, p2]:
            for border in [
                'top',
                'bottom',
                'right',
                'left'
            ]:
                axes.spines[border].set_visible(False)

        # Get DPI and assign dimmensions to figure
        DPI = float(profFig.get_dpi())
        profFig.set_size_inches(780 / DPI, 140 / DPI)

        # Clear, format and plot pressure Values
        p1.clear()
        p1.set_ylabel(
            'Pressure [Bars]',
            color=config['format']['red']
        )
        p1.set_xlim(
            round(min(timeLst)-0.5, 1),
            round(max(timeLst)+0.5, 1)
        )
        p1.set_ylim(
            0,
            12
        )
        p1.tick_params(
            axis='y',
            labelcolor=config['format']['red'],
            labelsize=config['format']['labelSize'] * 0.5,
            length=0,
            pad=10
        )
        p1.tick_params(
            axis='x',
            labelcolor=config['format']['color1'],
            labelsize=config['format']['labelSize'] * 0.5,
            length=0,
            pad=5
        )
        p1.plot(
            timeLst,
            pressureProfileLst,
            linewidth=2,
            color=config['format']['red']
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
            c=config['format']['red'],
            marker='o'
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
        profFig.subplots_adjust(top=0.95, bottom=0.10)

        # Declare profile frame components
        canvasProf = FigureCanvasTkAgg(
            profFig,
            master=profile
        )
        canvasProfile = canvasProf.get_tk_widget()
        buttonBack = customtkinter.CTkButton(
            profile,
            height=config['format']['buttonHeight'],
            width=config['format']['buttonWidth'],
            corner_radius=config['format']['buttonHeight'],
            text='Back',
            command=lambda: back(profile)
        )
        buttonClose = customtkinter.CTkButton(
            profile,
            height=config['format']['buttonHeight'],
            width=config['format']['buttonWidth'],
            corner_radius=config['format']['buttonHeight'],
            text='Close',
            command=close
        )
        buttonSave = customtkinter.CTkButton(
            profile,
            height=config['format']['buttonHeight'],
            width=config['format']['buttonWidth'],
            corner_radius=config['format']['buttonHeight'],
            text='Save',
            command=lambda: check_profile(
                profile,
                customProfile,
                tkProfileName
            )
        )
        labelProfileName = customtkinter.CTkLabel(
            profile,
            text='Profile Name:'
        )
        valueProfileName = customtkinter.CTkEntry(
            profile,
            textvariable=tkProfileName
        )
        labelExtractionDur = customtkinter.CTkLabel(
            profile,
            text='Extraction Duration [Sec.]:'
        )
        valueExtractionDur = customtkinter.CTkSlider(
            profile,
            from_=12,
            to=60,
            number_of_steps=48,
            variable=tkExtractionDur,
            orientation='horizontal',
            command=lambda value=tkExtractionDur,
            tkProfParams=tkProfParams,
            key='extractionDuration',
            customProfile=customProfile,
            canvasProf=canvasProf,
            p1=p1,
            p2=p2: plot_profile_callback(
                value,
                tkProfParams,
                key,
                customProfile,
                canvasProf,
                p1,
                p2,
                profFig
            )
        )
        labelPreInfusion = customtkinter.CTkLabel(
            profile,
            text='Pre-Infusion:'
        )
        labelPreDur = customtkinter.CTkLabel(
            profile,
            text='Duration [Sec.]:'
        )
        selectInfusionDuration = customtkinter.CTkOptionMenu(
            profile,
            variable=tkInfusionDur,
            values=[*[
                str(infusionDuration) for infusionDuration
                in infusionDurationLst
            ]],
            button_color=config['format']['blue'],
            button_hover_color=config['format']['blue'],
            command=lambda value=tkInfusionDur,
            tkProfParams=tkProfParams,
            key='infusionDuration',
            customProfile=customProfile,
            canvasProf=canvasProf,
            p1=p1,
            p2=p2: plot_profile_callback(
                value,
                tkProfParams,
                key,
                customProfile,
                canvasProf,
                p1,
                p2,
                profFig
            )
        )
        labelPrePres = customtkinter.CTkLabel(
            profile,
            text='Pressure [Bars]:'
        )
        selectInfusionPressure = customtkinter.CTkOptionMenu(
            profile,
            variable=tkInfusionPres,
            values=[*[
                str(infusionPressure) for infusionPressure
                in infusionPressureLst
            ]],
            button_color=config['format']['blue'],
            button_hover_color=config['format']['blue'],
            command=lambda value=tkInfusionPres,
            tkProfParams=tkProfParams,
            key='infusionPressure',
            customProfile=customProfile,
            canvasProf=canvasProf,
            p1=p1,
            p2=p2: plot_profile_callback(
                value,
                tkProfParams,
                key,
                customProfile,
                canvasProf,
                p1,
                p2,
                profFig
            )
        )
        labelP0 = customtkinter.CTkLabel(
            profile,
            text='P0:'
        )
        valueP0 = customtkinter.CTkSlider(
            profile,
            from_=1,
            to=12,
            number_of_steps=12,
            variable=tkP0,
            orientation='horizontal',
            command=lambda value=tkP0,
            tkProfParams=tkProfParams,
            key='p0',
            customProfile=customProfile,
            canvasProf=canvasProf,
            p1=p1,
            p2=p2: plot_profile_callback(
                value,
                tkProfParams,
                key,
                customProfile,
                canvasProf,
                p1,
                p2,
                profFig
            )
        )
        labelP1 = customtkinter.CTkLabel(
            profile,
            text='P1:'
        )
        valueP1 = customtkinter.CTkSlider(
            profile,
            from_=1,
            to=12,
            number_of_steps=12,
            variable=tkP1,
            orientation='horizontal',
            command=lambda value=tkP1,
            tkProfParams=tkProfParams,
            key='p1',
            customProfile=customProfile,
            canvasProf=canvasProf,
            p1=p1,
            p2=p2: plot_profile_callback(
                value,
                tkProfParams,
                key,
                customProfile,
                canvasProf,
                p1,
                p2,
                profFig
            )
        )
        labelP2 = customtkinter.CTkLabel(
            profile,
            text='P2:'
        )
        valueP2 = customtkinter.CTkSlider(
            profile,
            from_=1,
            to=12,
            number_of_steps=12,
            variable=tkP2,
            orientation='horizontal',
            command=lambda value=tkP2,
            tkProfParams=tkProfParams,
            key='p2',
            customProfile=customProfile,
            canvasProf=canvasProf,
            p1=p1,
            p2=p2: plot_profile_callback(
                value,
                tkProfParams,
                key,
                customProfile,
                canvasProf,
                p1,
                p2,
                profFig
            )
        )
        labelP3 = customtkinter.CTkLabel(
            profile,
            text='P3:'
        )
        valueP3 = customtkinter.CTkSlider(
            profile,
            from_=1,
            to=12,
            number_of_steps=12,
            variable=tkP3,
            orientation='horizontal',
            command=lambda value=tkP3,
            tkProfParams=tkProfParams,
            key='p3',
            customProfile=customProfile,
            canvasProf=canvasProf,
            p1=p1,
            p2=p2: plot_profile_callback(
                value,
                tkProfParams,
                key,
                customProfile,
                canvasProf,
                p1,
                p2,
                profFig
            )
        )
        labelP4 = customtkinter.CTkLabel(
            profile,
            text='P4:'
        )
        valueP4 = customtkinter.CTkSlider(
            profile,
            from_=1,
            to=12,
            number_of_steps=12,
            variable=tkP4,
            orientation='horizontal',
            command=lambda value=tkP4,
            tkProfParams=tkProfParams,
            key='p4',
            customProfile=customProfile,
            canvasProf=canvasProf,
            p1=p1,
            p2=p2: plot_profile_callback(
                value,
                tkProfParams,
                key,
                customProfile,
                canvasProf,
                p1,
                p2,
                profFig
            )
        )
        labelParams = customtkinter.CTkLabel(
            profile,
            textvariable=tkProfParams
        )

        # Pack profile frame components
        buttonBack.grid(
            column=0,
            row=0,
            columnspan=2,
            rowspan=1,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.W
        )
        buttonClose.grid(
            column=5,
            row=0,
            columnspan=2,
            rowspan=1,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E
        )
        buttonSave.grid(
            column=6,
            row=10,
            columnspan=2,
            rowspan=1,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E
        )
        canvasProfile.grid(
            column=0,
            row=1,
            columnspan=7,
            rowspan=4,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        labelProfileName.grid(
            column=1,
            row=5,
            columnspan=1,
            rowspan=1,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E
        )
        valueProfileName.grid(
            column=2,
            row=5,
            columnspan=2,
            rowspan=1,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        labelExtractionDur.grid(
            column=0,
            row=6,
            columnspan=2,
            rowspan=1,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E
        )
        valueExtractionDur.grid(
            column=2,
            row=6,
            columnspan=2,
            rowspan=1,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        labelPreInfusion.grid(
            column=1,
            row=7,
            columnspan=1,
            rowspan=1,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E
        )
        labelPreDur.grid(
            column=2,
            row=7,
            columnspan=1,
            rowspan=1,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E
        )
        selectInfusionDuration.grid(
            column=3,
            row=7,
            columnspan=1,
            rowspan=1,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        labelPrePres.grid(
            column=2,
            row=8,
            columnspan=1,
            rowspan=1,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E
        )
        selectInfusionPressure.grid(
            column=3,
            row=8,
            columnspan=1,
            rowspan=1,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        labelP0.grid(
            column=4,
            row=5,
            columnspan=1,
            rowspan=1,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E
        )
        valueP0.grid(
            column=5,
            row=5,
            columnspan=2,
            rowspan=1,
            padx=config['format']['padX'] + 10,
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        labelP1.grid(
            column=4,
            row=6,
            columnspan=1,
            rowspan=1,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E
        )
        valueP1.grid(
            column=5,
            row=6,
            columnspan=2,
            rowspan=1,
            padx=config['format']['padX'] + 10,
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        labelP2.grid(
            column=4,
            row=7,
            columnspan=1,
            rowspan=1,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E
        )
        valueP2.grid(
            column=5,
            row=7,
            columnspan=2,
            rowspan=1,
            padx=config['format']['padX'] + 10,
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        labelP3.grid(
            column=4,
            row=8,
            columnspan=1,
            rowspan=1,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E
        )
        valueP3.grid(
            column=5,
            row=8,
            columnspan=2,
            rowspan=1,
            padx=config['format']['padX'] + 10,
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        labelP4.grid(
            column=4,
            row=9,
            columnspan=1,
            rowspan=1,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E
        )
        valueP4.grid(
            column=5,
            row=9,
            columnspan=2,
            rowspan=1,
            padx=config['format']['padX'] + 10,
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.E+tk.W
        )
        labelParams.grid(
            column=0,
            row=10,
            columnspan=6,
            rowspan=1,
            padx=config['format']['padX'],
            pady=config['format']['padY'],
            sticky=tk.N+tk.S+tk.W
        )


# Main
if __name__ == '__main__':

    # Initialize the application window
    theme = utils.read_config(
        configLoc=os.path.join(
            config['session']['assetsLoc'],
            'app',
            'dark-blue.json'
        )
    )
    customtkinter.set_appearance_mode("light")
    customtkinter.set_default_color_theme(
        os.path.join(
            config['session']['assetsLoc'],
            'app',
            'dark-blue.json'
        )
    )
    root = customtkinter.CTk()
    root.title('Ospro')
    root.geometry(
        "{}x{}+{}+{}".format(
            config['format']['width'],
            config['format']['height'],
            int((root.winfo_screenwidth()/2) - (config['format']['width']/2)),
            int((root.winfo_screenheight()/2) - (config['format']['height']/2))
        )
    )
    root.grid_columnconfigure(
        8,
        minsize=int(
            config['format']['buttonWidth'] +
            config['format']['padX'] +
            config['format']['padX']
        )
    )
    root.grid_rowconfigure(
        12,
        minsize=int(
            config['format']['buttonHeight'] +
            config['format']['padY'] +
            config['format']['padY']
        )
    )

    if not config['session']['dev']:
        root.attributes('-fullscreen', True)
        root.configure(cursor='none')

    # Apply formats from ~/assets/app/
    if sys.platform == 'darwin':
        config['format']['font'] = theme['CTkFont']['macOS']['family']
        config['format']['labelSize'] = theme['CTkFont']['macOS']['size']
        config['format']['buttonSize'] = theme['CTkFont']['macOS']['size']
    elif sys.platform == 'win32':
        config['format']['font'] = theme['CTkFont']['Windows']['family']
        config['format']['labelSize'] = theme['CTkFont']['Windows']['size']
        config['format']['buttonSize'] = theme['CTkFont']['Windows']['size']
    else:
        config['format']['font'] = theme['CTkFont']['Linux']['family']
        config['format']['labelSize'] = theme['CTkFont']['Linux']['size']
        config['format']['buttonSize'] = theme['CTkFont']['Linux']['size']

    config['format']['color1'] = theme['CTkLabel']['text_color'][0]
    config['format']['color3'] = theme['CTkFrame']['fg_color'][0]
    config['format']['color4'] = theme['CTk']['fg_color'][0]
    config['format']['blue'] = theme['CTkButton']['fg_color'][0]

    # Declair main frame
    mainFrame = customtkinter.CTkFrame(
        root,
        width=config['format']['width'],
        height=config['format']['height']
    )
    mainFrame.pack(
        fill=tk.BOTH,
        expand=True
    )
    for c in range(0, 7):
        mainFrame.columnconfigure(
            c,
            minsize=90,
            weight=1
        )
    for r in range(0, 11):
        mainFrame.rowconfigure(
            r,
            minsize=30,
            weight=1
        )

    # Store config selections
    tkCounter = tk.DoubleVar(root)
    tkCounter.set(float(counter))

    tkScale = tk.StringVar(root)
    scaleLst = ['Fahrenheit [F]', 'Celcius [C]']
    tkScale.set(config['settings']['scaleLabel'])

    tkSetPoint = tk.DoubleVar(root)

    # Assign temperature range based on scale value
    if config['settings']['scale'] == 'F':
        setPointLst = list(np.arange(205, 226, 1))
    else:
        setPointLst = [
            round(item, 1)
            for item in list(
                np.arange(96, 109, 0.5)
            )
        ]

    tkSetPoint.set(config['tPID']['setPoint'])

    tkProfile = tk.StringVar(root)

    # Check if pressure profile config exists
    try:
        pressureProfile = utils.read_config(
            configLoc=os.path.join(
                config['session']['configLoc'],
                'profiles',
                '.'.join([
                    config['settings']['profile'],
                    'json'
                ])
            )
        )
    except FileNotFoundError:
        assign_profile(
            profile={
                'settings': {
                    'profileName': 'Manual',
                    'extractionDuration': 0.0,
                    'infusionDuration': 0,
                    'infusionPressure': 0,
                    'p0': 0,
                    'p1': 0,
                    'p2': 0,
                    'p3': 0,
                    'p4': 0,
                    'timeLst': [],
                    'pressureProfileLst': []
                }
            }
        )
        print("WARNING: Pressure profile reset to default 'Manual' profile.")

    tkProfile.set(config['settings']['profile'])

    tkFlush = tk.IntVar(root)
    flushLst = list(range(1, 6))
    tkFlush.set(config['settings']['flush'])

    # Set initial sensor values
    tkTempValue = tk.IntVar(root)
    tkTempValue.set(tSensor.read_temp(config))

    tkPresValue = tk.DoubleVar(root)
    tkPresValue.set(pSensor.read_pressure(config))

    # Declare main frame components
    buttonClose = customtkinter.CTkButton(
        mainFrame,
        height=config['format']['buttonHeight'],
        width=config['format']['buttonWidth'],
        corner_radius=config['format']['buttonHeight'],
        text='Close',
        command=close
    )
    buttonPower = customtkinter.CTkButton(
        mainFrame,
        height=config['format']['buttonHeight']*2,
        width=config['format']['buttonWidth']*2,
        corner_radius=config['format']['buttonHeight'],
        text='Power',
        command=button_press,
        state='disabled'
    )
    buttonDash = customtkinter.CTkButton(
        mainFrame,
        height=config['format']['buttonHeight']*2,
        width=config['format']['buttonWidth']*2,
        corner_radius=config['format']['buttonHeight'],
        text='Dashboard',
        command=create_dashboard
    )
    buttonSettings = customtkinter.CTkButton(
        mainFrame,
        height=config['format']['buttonHeight']*2,
        width=config['format']['buttonWidth']*2,
        corner_radius=config['format']['buttonHeight'],
        text='Settings',
        command=create_settings
    )
    labelTemp = customtkinter.CTkLabel(
        mainFrame,
        textvariable=tkScale
    )
    valueTemp = customtkinter.CTkLabel(
        mainFrame,
        textvariable=tkTempValue,
        font=(
            config['format']['font'],
            config['format']['labelSize'],
            'bold'
        ),
        text_color=config['format']['blue']
    )
    labelPres = customtkinter.CTkLabel(
        mainFrame,
        text='Pressure [Bars]'
    )
    valuePres = customtkinter.CTkLabel(
        mainFrame,
        textvariable=tkPresValue,
        font=(
            config['format']['font'],
            config['format']['labelSize'],
            'bold'
        ),
        text_color=config['format']['red']
    )
    labelProfile = customtkinter.CTkLabel(
        mainFrame,
        text='Profile:'
    )
    valueProfile = customtkinter.CTkLabel(
        mainFrame,
        textvariable=tkProfile
    )

    # Pack Main Components
    buttonClose.grid(
        column=5,
        row=0,
        columnspan=2,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    buttonPower.grid(
        column=2,
        row=7,
        columnspan=1,
        rowspan=2,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonDash.grid(
        column=3,
        row=7,
        columnspan=1,
        rowspan=2,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonSettings.grid(
        column=4,
        row=7,
        columnspan=1,
        rowspan=2,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E+tk.W
    )
    buttonClose.grid(
        column=5,
        row=0,
        columnspan=2,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    labelTemp.grid(
        column=0,
        row=10,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    valueTemp.grid(
        column=1,
        row=10,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    labelPres.grid(
        column=2,
        row=10,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    valuePres.grid(
        column=3,
        row=10,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.W
    )
    labelProfile.grid(
        column=4,
        row=10,
        columnspan=1,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.E
    )
    valueProfile.grid(
        column=5,
        row=10,
        columnspan=2,
        rowspan=1,
        padx=config['format']['padX'],
        pady=config['format']['padY'],
        sticky=tk.N+tk.S+tk.W
    )

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
            root.after(100, idle)
            root.mainloop()

        except KeyboardInterrupt:

            # Terminate dashboard
            root.quit()

            # Cleanup
            if not config['session']['dev']:
                GPIO.cleanup()

            # Exit
            sys.exit()

    # Terminate dashboard
    root.quit()

    # Cleanup
    if not config['session']['dev']:
        GPIO.cleanup()
