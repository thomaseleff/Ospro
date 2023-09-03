"""
Information
---------------------------------------------------------------------
Name        : pressure_profile_fitting_algorithm.py
Location    : ~/modules/
Author      : Tom Eleff
Published   : 2023-08-25
Revised on  : ~

Description
---------------------------------------------------------------------
Identifies the pressure profile settings based on a user-generted
profile time-series.
"""

# Import modules
import os
import time
import scipy
import datetime as dt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from numpy.core.multiarray import interp as compiled_interp
# from rdp import rdp
import utils.utils as utils

# Findings
# (1) np.meshgrid() is ~6x faster than itertools.product()
#   for smaller combinations (100,000), but ~0.8x slower
#   for larger combinations (312,500,000). Run-time is
#   relatively similar at moderate combinations (24,300,300).
#
# (2) With np.meshgrid() and np.apply_along_axis() the
#   simulate_profiles() method is ~22.4x faster than the
#   previous method.
#
# (3) Linear interpolation using compiled_interp() within
#   the simulate_profiles() method is ~ 1.02x faster
#   than np.interp().


# @utils.run_time
def reduce(
    x,
    y,
    EPSILON=0.7,
    INFUSION_LIMIT=3,
    START_DELAY=1,
    INFUSION_DURATION_LIMIT=10
):
    """
    Variables
    ---------------------------------------------------------------------
    x                       = <np.array()> Vector of the Time series
    y                       = <np.array()> Vector of the Pressure series
    EPSILON                 = <float> Overall degree of
                                simplification applied in the
                                RDP algorithm.
    INFUSION_LIMIT          = <int> Maximum pressure (bars)
                                considered to be pre-infusion.
    START_DELAY             = <int> Period of duration in time (seconds)
                                to omit from the expresso extraction
                                time-series.

    Description
    ---------------------------------------------------------------------
    Simplifies the espresso extraction time-series, using the
    Ramer-Douglas-Peucker (RDP) algorithm, to identify local pressure
    values for the simulation and selection of the best fitted pressure
    profile.
    """

    # Apply smoothing
    ysmoothed = np.array(
        scipy.ndimage.uniform_filter1d(
            y,
            size=7,
            mode='reflect'
        )
    )

    # Reduce the pressure data using Ramer-Douglas-Peucker
    # yreduced = np.unique(
    #     np.round(
    #         rdp(
    #             M=np.concatenate(
    #                 [x[:, None], ysmoothed[:, None]],
    #                 axis=1
    #             ),
    #             epsilon=EPSILON
    #         ),
    #         decimals=0
    #     ).transpose()[1]
    # )

    # Determine the first index where pressure exceeds
    #   the pre-infusion pressure limit
    INFUSION_DURATION_INDEX = np.round(
        np.argmax(
            ysmoothed[
                np.round(START_DELAY * 10, decimals=0):
            ] >= INFUSION_LIMIT
        ) + np.round(START_DELAY * 10, decimals=0),
        decimals=0
    )

    # Evaluate pre-infusion
    if (
        (ysmoothed.shape[0] >= INFUSION_DURATION_LIMIT) and
        (
            INFUSION_DURATION_INDEX > np.round(
                START_DELAY * 10, decimals=0
            )
        )
    ):

        # Derive pre-infusion duration values
        xti = reduce_range(
            a=x[
                np.round(
                    INFUSION_DURATION_INDEX - 10,
                    decimals=0
                ):INFUSION_DURATION_INDEX
            ]
        )

        # np.arange(
        #     start=np.floor(
        #         x[INFUSION_DURATION_INDEX]
        #     ),
        #     stop=np.round(
        #         np.ceil(x[INFUSION_DURATION_INDEX]) + 1,
        #         decimals=0
        #     ),
        #     step=1
        # )

        # Derive local pre-infusion pressure values from rdp
        # yinfusion = np.arange(
        #     start=np.min(yreduced[yreduced <= INFUSION_LIMIT]),
        #     stop=np.round(
        #         np.max(yreduced[yreduced <= INFUSION_LIMIT]) + 1,
        #         decimals=0
        #     ),
        #     step=1
        # )

        # Derive local extraction pressure values
        ypi = reduce_range(a=ysmoothed[:np.where(x == xti[-1])[0][0]])
        yp0, yp1, yp2, yp3, yp4 = derive_local_extraction_pressure_ranges(
            x=x,
            y=ysmoothed,
            xti=xti
        )
        yp0 = reduce_range(a=yp0)
        yp1 = reduce_range(a=yp1)
        yp2 = reduce_range(a=yp2)
        yp3 = reduce_range(a=yp3)
        yp4 = reduce_range(a=yp4)

    else:

        # Derive pre-infusion duration values
        xti = np.array([0])

        # Derive local extraction pressure values
        ypi = np.array([])
        yp0, yp1, yp2, yp3, yp4 = derive_local_extraction_pressure_ranges(
            x=x,
            y=ysmoothed,
            xti=xti
        )
        yp0 = reduce_range(a=yp0)
        yp1 = reduce_range(a=yp1)
        yp2 = reduce_range(a=yp2)
        yp3 = reduce_range(a=yp3)
        yp4 = reduce_range(a=yp4)

    # Derive local extraction pressure values
    # try:
    #     yextraction = np.arange(
    #         start=np.min(yreduced[yreduced > INFUSION_LIMIT]),
    #         stop=np.round(
    #             np.max(yreduced[yreduced > INFUSION_LIMIT]) + 1,
    #             decimals=0
    #         ),
    #         step=1
    #     )
    # except ValueError:
    #     yextraction = np.arange(
    #         start=1,
    #         stop=np.round(INFUSION_LIMIT + 1, decimals=0),
    #         step=1
    #     )

    # Return local pressure values
    return xti, ypi, yp0, yp1, yp2, yp3, yp4, ysmoothed


def derive_local_extraction_pressure_ranges(
    x,
    y,
    xti
):
    """
    Variables
    ---------------------------------------------------------------------
    x                       = <np.array()> Vector of the Time series
    y                       = <np.array()> Vector of the Pressure series
    xti                     = <np.array()> Vector of possible pre-infusion
                                duration values (seconds)

    Description
    ---------------------------------------------------------------------
    Returns a range of unique intager values from {a}.
    """

    return np.array_split(
        ary=y[np.where(x == xti[-1])[0][0]:],
        indices_or_sections=5
    )


def reduce_range(
    a
):
    """
    Variables
    ---------------------------------------------------------------------
    a                       = <np.array()> Vector

    Description
    ---------------------------------------------------------------------
    Returns a range of unique intager values from {a}.
    """

    return np.arange(
        start=np.floor(np.min(a)),
        stop=np.round(
            np.ceil(np.max(a) + 1),
            decimals=0
        ),
        step=1
    )


def simulate_profiles(
    x,
    xti,
    ypi,
    yp0,
    yp1,
    yp2,
    yp3,
    yp4,
):
    """
    Variables
    ---------------------------------------------------------------------
    x                       = <np.array()> Vector of the Time series
    xti                     = <np.array()> Vector of possible pre-infusion
                                duration values (seconds)
    ypi                     = <np.array()> Vector of possible pre-infusion
                                pressure values (bars)
    yp0                     = <np.array()> Vector of possible extraction
                                pressure values (bars) for the 1st quartile
    yp1                     = <np.array()> Vector of possible extraction
                                pressure values (bars) for the 2nd quartile
    yp2                     = <np.array()> Vector of possible extraction
                                pressure values (bars) for the 3rd quartile
    yp3                     = <np.array()> Vector of possible extraction
                                pressure values (bars) for the 4th quartile
    yp4                     = <np.array()> Vector of possible extraction
                                pressure values (bars) for the 5th quartile

    Description
    ---------------------------------------------------------------------
    Simulates espresso extraction profiles.
    """

    # Initialize simulation objects
    profiles = []
    maty0 = np.array([[]]).reshape(0, x.shape[0])

    # Simulate pre-infusion pressure profiles
    if ypi.shape[0] > 0:
        sinfusion = np.array(
            np.meshgrid(
                xti,
                ypi,
                yp0,
                yp1,
                yp2,
                yp3,
                yp4
            )
        ).transpose().reshape(-1, 7)

        profiles = profiles + sinfusion.tolist()

        maty0 = np.concatenate(
            (
                maty0,
                np.apply_along_axis(
                    func1d=interpolate,
                    axis=1,
                    arr=sinfusion,
                    x=x
                )
            ),
            axis=0
        )

    # Simulate extraction pressure profiles
    else:
        sextraction = np.array(
            np.meshgrid(
                yp0,
                yp1,
                yp2,
                yp3,
                yp4
            )
        ).transpose().reshape(-1, 5)

        profiles = profiles + sextraction.tolist()

        maty0 = np.concatenate(
            (
                maty0,
                np.apply_along_axis(
                    func1d=interpolate,
                    axis=1,
                    arr=sextraction,
                    x=x
                )
            ),
            axis=0
        )

    return maty0, profiles


def interpolate(
    a,
    x
):
    """
    Variables
    ---------------------------------------------------------------------
    a                       = <np.array()> Simulated espresso extraction
                                parameters in the following order,
                                {inf. dur}, {inf. pres}, {p0}, {p1}, {p2},
                                {p3}, {p4}. With pre-infusion {a} has
                                shape (7, ). Otherwise shape (5, ).
    x                       = <np.array()> Vector of the Time series

    Description
    ---------------------------------------------------------------------
    Derives a possible extraction profile as a linear interpolation.
    """

    # Generate the x and y coordinates for a pre-infusion pressure profile
    #   xp = np.array([0          , {inf. dur} , {p0}, {p1}, {p2}, {p3}, {p4}])
    #   fp = np.array([{inf. pres}, {inf. pres}, {p0}, {p1}, {p2}, {p3}, {p4}])
    if a.shape[0] > 5:
        xp = np.concatenate(
            (
                np.array([0, a[0]]),
                np.array(calculate_quartiles(
                        a=a,
                        xduration=x[-1]
                    )
                )
            )
        )
        fp = np.concatenate(
            (
                np.array([a[1], a[1]]),
                a[2:]
            ),
            axis=None
        )

    # Generate the x and y coordinates for an extraction pressure profile
    #   xp = np.array([{p0}, {p1}, {p2}, {p3}, {p4}])
    #   fp = np.array([{p0}, {p1}, {p2}, {p3}, {p4}])
    else:
        xp = calculate_quartiles(
            a=a,
            xduration=x[-1]
        )
        fp = np.copy(a)

    # Derive a possible pressure profile as a linear interpolation
    return compiled_interp(
        x=x,
        xp=xp,
        fp=fp
    )


def calculate_quartiles(
    a,
    xduration,
):
    """
    Variables
    ---------------------------------------------------------------------
    a                       = <np.array()> Simulated espresso extraction
                                parameters in the following order,
                                {inf. dur}, {inf. pres}, {p0}, {p1}, {p2},
                                {p3}, {p4}. With pre-infusion {a} has
                                shape (7, ). Otherwise shape (5, ).
    xduration               = <float> The value of the duration of the
                                time series

    Description
    ---------------------------------------------------------------------
    Calculates the quartiles of the espresso extraction time series
    for linear interpolation.
    """

    # Derive the start time from the simulated espresso extraction parameters
    if a.shape[0] > 5:
        x0 = np.round(a[0] + 1, decimals=0)
    else:
        x0 = 0

    # Return the x coordinates of the espresso extraction quartiles
    return np.quantile(
        np.arange(
            start=x0,
            stop=np.round(
                xduration + 0.1,
                decimals=1
            ),
            step=0.1
        ),
        q=np.array([0, 0.25, 0.5, 0.75, 1]),
        axis=0
    )


def fit_profile(
    maty0,
    y
):
    """
    Variables
    ---------------------------------------------------------------------
    maty0                   = <np.array()> Simulated espresso extraction
                                profiles
    y                       = <np.array()> Pressure series

    Description
    ---------------------------------------------------------------------
    Returns the simulated pressure profile with the minimal
    square root of the sum of absolute squared error with the
    pressure series.
    """

    # Calculate the frobenius norm of the error
    sse = np.linalg.norm(maty0-y, axis=1)
    id = np.argmin(sse)

    return {
        'id': id,
        'sse': np.round(sse[id], 6),
        'simulations': sse.shape[0]
    }


# @utils.run_time
def pressure_profile_fitting_algorithm(
    x,
    y
):
    """
    Variables
    ---------------------------------------------------------------------
    x                       = <np.array()> Vector of the Time series
    y                       = <np.array()> Vector of the Pressure series

    Description
    ---------------------------------------------------------------------
    Performs an ML and OLS algorithm that determines the best fitted
    pressure profile from espresso extraction time series
    data.
    """

    # Perform the Ramer-Douglas-Peucker ML algorithm to,
    #   determine the possible local infusion and extraction
    #   pressure values
    xti, ypi, yp0, yp1, yp2, yp3, yp4, ysmoothed = reduce(x=x, y=y)
    # print(yinfusion, yextraction)
    # yinfusion, yextraction = reduce2(x=x, y=y)
    # yinfusion, yextraction = reduce3(x=x, y=y)

    # xinfusion = np.array([1, 2, 3, 4, 5, 6])

    # Simulate the possible espresso extraction profiles
    maty0, profiles = simulate_profiles(
        x=x,
        xti=xti,
        ypi=ypi,
        yp0=yp0,
        yp1=yp1,
        yp2=yp2,
        yp3=yp3,
        yp4=yp4
    )

    # Perform the OLS algorithm to,
    #   determine the pressure profile with the minimum
    #   error with the espresso extraction series data
    solution = fit_profile(
        maty0=maty0,
        y=y
    )

    # Unpack the solution
    if len(profiles[solution['id']]) > 5:
        infusionDuration, infusionPressure, p0, p1, p2, p3, p4 = (
            profiles[solution['id']]
        )
    else:
        infusionDuration = 0
        infusionPressure = 3
        p0, p1, p2, p3, p4 = (
            profiles[solution['id']]
        )

    return {
        'settings': {
            'name': 'User_1',
            'type': 'User',
            'extractionDuration': x[-1],
            'infusionDuration': infusionDuration,
            'infusionPressure': infusionPressure,
            'p0': p0,
            'p1': p1,
            'p2': p2,
            'p3': p3,
            'p4': p4,
            'timeLst': x.tolist(),
            'pressureProfileLst': np.round(
                maty0[solution['id']],
                1
            ).tolist(),
            'pressureSeries': y.tolist(),
            'pressureSeriesSmoothed': ysmoothed
        },
        'ppfa': solution
    }


def plot_solution(
    config,
    solution,
    fileName
):
    """
    Variables
    ---------------------------------------------------------------------
    solution                = <dict> Dictionary object of the fitted
                                solution
    quartiles               = <list> List object of the pressure profile
                                node quartiles
    fileName                = <str> Prefix for the plot file name
    scenario                = <int> Scenario ID

    Description
    ---------------------------------------------------------------------
    Imputes the pressure profile nodes based on the {solution} and
    smoothed pressure time series and returns the quartiles.
    """

    if solution['settings']['infusionDuration'] == 0:
        scatterXLst = calculate_quartiles(
            a=np.array([
                solution['settings']['p0'],
                solution['settings']['p1'],
                solution['settings']['p2'],
                solution['settings']['p3'],
                solution['settings']['p4']
            ]),
            xduration=solution['settings']['extractionDuration']
        ).tolist()
        scatterYLst = [
            solution['settings']['p0'],
            solution['settings']['p1'],
            solution['settings']['p2'],
            solution['settings']['p3'],
            solution['settings']['p4']
        ]
    else:
        scatterXLst = [
            0,
            solution['settings']['infusionDuration']
         ] + calculate_quartiles(
            a=np.array([
                solution['settings']['infusionDuration'],
                solution['settings']['infusionPressure'],
                solution['settings']['p0'],
                solution['settings']['p1'],
                solution['settings']['p2'],
                solution['settings']['p3'],
                solution['settings']['p4']
            ]),
            xduration=solution['settings']['extractionDuration']
        ).tolist()
        scatterYLst = [
            solution['settings']['infusionPressure'],
            solution['settings']['infusionPressure'],
            solution['settings']['p0'],
            solution['settings']['p1'],
            solution['settings']['p2'],
            solution['settings']['p3'],
            solution['settings']['p4']
        ]

    fig = plt.figure()
    x1 = fig.add_subplot(1, 1, 1)
    plt.figtext(
        0.15,
        0.95,
        'Run-time: %s hh:mm:ss' % (
            str(solution['ppfa']['runTime'])
        )
    )
    plt.figtext(
        0.15,
        0.90,
        'Sq-Root of the Sum of Squared Error: %s' % (
            round(solution['ppfa']['sse'], 2)
        )
    )

    # Clear, format and plot profile values
    x1.clear()
    x1.set_ylabel(
        'Pressure (bars)'
    )
    x1.set_xlabel(
        'Time (seconds)'
    )
    x1.set_xlim(
        min(solution['settings']['timeLst']),
        max(solution['settings']['timeLst'])
    )
    x1.set_ylim(
        0,
        12
    )
    x1.tick_params(
        axis='y',
        length=0,
        pad=10
    )
    x1.tick_params(
        axis='x',
        length=0,
        pad=10
    )
    x1.plot(
        solution['settings']['timeLst'],
        (
            solution['settings']['pressureSeries']
            [:len(solution['settings']['timeLst'])]
        ),
        color='blue',
        alpha=0.25,
        linewidth=1,
        label='Observed'
    )
    x1.plot(
        solution['settings']['timeLst'],
        (
            solution['settings']['pressureSeriesSmoothed']
            [:len(solution['settings']['timeLst'])]
        ),
        color='blue',
        alpha=0.5,
        linewidth=1,
        label='Smoothed'
    )
    x1.plot(
        solution['settings']['timeLst'],
        (
            solution['settings']['pressureProfileLst']
            [:len(solution['settings']['timeLst'])]
        ),
        color='blue',
        alpha=1,
        linewidth=1,
        label='Profile'
    )
    x1.scatter(
        scatterXLst,
        scatterYLst,
        color='red',
        label='Solution',
        marker='o',
        s=25
    )
    x1.set_xticks(
        ticks=np.arange(
            min(solution['settings']['timeLst']),
            np.ceil(max(solution['settings']['timeLst'])),
            1
        )
    )
    x1.legend(loc='upper right')

    # Save
    plt.savefig(
        os.path.join(
            config['outputs']['path'],
            config['outputs']['root'],
            'plots',
            '.'.join([
                '_'.join([
                    fileName,
                    str(solution['ppfa']['simulations']),
                    str(solution['ppfa']['id'])
                ]),
                'jpeg'
            ])
        )
    )
    plt.close('all')


if __name__ == '__main__':

    # Initialize global variables
    dirName = os.path.join(
        os.path.join(os.path.dirname(__file__), os.pardir),
        'diagnostics'
    )
    config = {
        "outputs": {
            'path': os.path.join(
                os.path.join(os.path.dirname(__file__), os.pardir),
                'simulation'
            ),
            'root': dt.datetime.now().strftime("%Y-%m-%d %I-%M-%S%p"),
            'subFolders': ['plots', 'results']
        }
    }
    caseIDs = {
        '408': 'Slowest, reduce()',
        '573': 'Highest simulations & error, reduce()',
        '412': 'Highest simulations & error & slowest, reduce2()',
        '618': 'High error, reduce() & reduce2()',
        '659': (
            'Fastest & shortest extraction & no pre-infusion ' +
            '& lowest error, reduce()'
        ),
        '658': 'Fastest & shortest extraction & no pre-infusion, reduce2()',
        '198': 'Lowest error, reduce2()',
        '447': 'Highest error, reduce() v2',
        '312': 'Low pressure extraction at the end, reduce() v2'
    }

    # Generate the output directory
    utils.generate_output_directory(
        config=config
    )

    # Generate the results output
    with open(
        os.path.join(
            config['outputs']['path'],
            config['outputs']['root'],
            'results',
            'results.csv'
        ),
        'a'
    ) as f:
        f.write(
            ','.join([
                'name',
                'num_simulations',
                'solution_id',
                'time_to_solve',
                'sse',
                'extraction_duration',
                'infusion_duration',
                'infusion_pressure',
                'p0',
                'p1',
                'p2',
                'p3',
                'p4'
            ]) + '\n'
        )

    # Evaluate espresso extraction data
    for file in os.listdir(dirName):
        if '.csv' in file:
            if file.split('_')[1] in list(caseIDs.keys()):

                # Import extraction data series
                df = pd.read_csv(
                    os.path.join(dirName, file),
                    sep=','
                )
                x = df['Duration'].to_numpy()
                y = df['Pressure'].to_numpy()

                # Call the pressure profile fitting algorithm
                t1 = time.time()
                solution = pressure_profile_fitting_algorithm(x=x, y=y)
                t2 = time.time()
                td = dt.timedelta(seconds=(t2-t1))

                # Preserve execution time
                solution['ppfa']['runTime'] = td

                # Plot
                plot_solution(
                    config=config,
                    solution=solution,
                    fileName=file.split('.')[0]
                )

                # Output result
                with open(
                    os.path.join(
                        config['outputs']['path'],
                        config['outputs']['root'],
                        'results',
                        'results.csv'
                    ),
                    'a'
                ) as f:
                    f.write(
                        ','.join([
                            '_'.join([
                                file.split('.')[0],
                                str(solution['ppfa']['id'])
                            ]),
                            str(solution['ppfa']['simulations']),
                            str(solution['ppfa']['id']),
                            ' '.join([
                                str(solution['ppfa']['runTime']),
                                'hh:mm:ss'
                            ]),
                            str(solution['ppfa']['sse']),
                            str(solution['settings']['extractionDuration']),
                            str(solution['settings']['infusionDuration']),
                            str(solution['settings']['infusionPressure']),
                            str(solution['settings']['p0']),
                            str(solution['settings']['p1']),
                            str(solution['settings']['p2']),
                            str(solution['settings']['p3']),
                            str(solution['settings']['p4'])
                        ]) + '\n'
                    )

                # Log
                print(
                    "{:<{len0}} {:<{len1}} {:<{len2}}".format(
                        'File: %s' % (file.split('.')[0]),
                        'SE: %.6f' % (solution['ppfa']['sse']),
                        'Profile: [%s, %s, %s, %s, %s, %s, %s, %s]' % (
                            solution['settings']['extractionDuration'],
                            solution['settings']['infusionDuration'],
                            solution['settings']['infusionPressure'],
                            solution['settings']['p0'],
                            solution['settings']['p1'],
                            solution['settings']['p2'],
                            solution['settings']['p3'],
                            solution['settings']['p4']
                        ),
                        len0=33,
                        len1=15,
                        len2=58
                    )
                )
