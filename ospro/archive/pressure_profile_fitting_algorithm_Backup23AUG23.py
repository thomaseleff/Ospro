"""
Information
---------------------------------------------------------------------
Name        : pressure_profile_fitting_algorithm.py
Location    : ~/modules/
Author      : Tom Eleff
Published   : 2023-07-11
Revised on  : ~

Description
---------------------------------------------------------------------
Identifies the pressure profile settings based on a user-generted
profile time-series.
"""

# Import modules
import os
import scipy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import itertools
import random
import datetime

import utils.utils as utils
from dashboard import calculate_profile_quartile


# Define simulation functions
@utils.run_time
def simulate_pressure_profiles(
    config,
    scenarioLst,
    fileName
):
    """
    Variables
    ---------------------------------------------------------------------
    config                  = <dict> Dictionary object containing the
                                output directory paths
    scenarioLst             = <list> List of pressure profile scenarios
    fileName                = <str> Config file name

    Description
    ---------------------------------------------------------------------
    Generates {fileName}.json within ~/simulation/config that contains the
    cross-combination of all pressure profile settings within
    {scenarioLst}.
    """

    # Print Status
    print("Simulating %s pressure profiles" % (len(scenarioLst)))

    scenarios = {}

    for item in scenarioLst:

        # Print Status
        # if round(scenarioLst.index(item) % 1000, 0) == 0:
        #     print(scenarioLst.index(item))

        scenarios[scenarioLst.index(item)] = {
            "name": scenarioLst.index(item),
            "type": "Simulation",
            "extractionDuration": item[0],
            "infusionDuration": item[1],
            "infusionPressure": item[2],
            "p0": item[3],
            "p1": item[4],
            "p2": item[5],
            "p3": item[6],
            "p4": item[7]
        }

        # Output result
        with open(
            os.path.join(
                config['outputs']['path'],
                config['outputs']['root'],
                'results',
                'results.csv'
            ),
            'a'
        ) as file:
            file.write(','.join([
                '_'.join([
                    fileName.split('.')[0],
                    str(scenarios[scenarioLst.index(item)]['name'])
                ]),
                scenarios[scenarioLst.index(item)]['type'],
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                str(scenarios[scenarioLst.index(item)]['extractionDuration']),
                str(scenarios[scenarioLst.index(item)]['infusionDuration']),
                str(scenarios[scenarioLst.index(item)]['infusionPressure']),
                str(scenarios[scenarioLst.index(item)]['p0']),
                str(scenarios[scenarioLst.index(item)]['p1']),
                str(scenarios[scenarioLst.index(item)]['p2']),
                str(scenarios[scenarioLst.index(item)]['p3']),
                str(scenarios[scenarioLst.index(item)]['p4'])
            ]) + '\n')

    utils.write_config(
        configLoc=os.path.join(
            config['outputs']['path'],
            config['outputs']['root'],
            'config',
            fileName
        ),
        config=scenarios
    )


@utils.run_time
def fit_pressure_profile(
    config,
    profiles,
    scenarioLst,
    fileName,
    plot,
    PARAMS
):
    """
    Variables
    ---------------------------------------------------------------------
    config                  = <dict> Dictionary object containing the
                                output directory paths
    profiles                = <dict> Dictionary of simulated pressure
                                profile scenarios
    scenarioLst             = <list> List of pressure profile scenarios
    fileName                = <str> Config file name
    plot                    = <bool> Outputs plots when enabled
    PARAMS                  = <dictionary> Pressure profile fitting
                                algorithm parameters

    Description
    ---------------------------------------------------------------------
    Imports {fileName}.json within ~/config/simulation, generates the
    time series data and evaluates all solutions and generates a result.
    """

    # Iterate through scenarioLst
    for scenario in scenarioLst:

        # Create simulation profile config
        profile = {}
        profile['settings'] = profiles[scenario]

        # Create time series list
        timeLst = list(
            np.arange(
                0,
                float(profile['settings']['extractionDuration']),
                0.1
            )
        )
        timeLst = [round(item, 1) for item in timeLst]
        profile['settings']['timeLst'] = timeLst

        # Return pressure profile and quartiles
        #   Ignore scatterXLst, as the solution should derive this separately
        pressureProfileLst, scatterXLst = calculate_profile_quartile(
            profile,
            timeLst
        )
        profile['settings']['pressureProfileLst'] = pressureProfileLst

        # Apply smoothing
        smoothedProfileLst = scipy.ndimage.uniform_filter1d(
            profile['settings']['pressureProfileLst'],
            size=7,
            mode='reflect'
        )

        # (i) Determine pre-infusion period
        solution = {}
        solution['settings'] = {
            'name': scenario,
            'type': 'Solution',
            'extractionDuration': (
                profile['settings']['extractionDuration']
            )
        }
        solution = pre_infusion_fitting_algorithm(
            solution=solution,
            x=profile['settings']['timeLst'],
            y=smoothedProfileLst,
            **PARAMS
        )

        # (ii) Determine pressure profile nodes
        solution, quartiles = impute_pressure_nodes(
            solution=solution,
            profile=profile,
            smoothedProfileLst=smoothedProfileLst
        )

        solution['settings']['timeLst'] = profile['settings']['timeLst']
        solution['settings']['pressureProfileLst'] = (
            profile['settings']['pressureProfileLst']
        )
        solution['settings']['smoothedProfileLst'] = (
            smoothedProfileLst.tolist()
        )

        # Calculate the error
        solution = calculate_sse(
            solution=solution,
            profile=profile
        )

        # (iii) Plot
        if plot:
            plot_solution(
                solution=solution,
                quartiles=quartiles,
                fileName=fileName.split('.')[0],
                scenario=scenario,
                paramLst=(
                    ','.join([
                        '('+str(PARAMS['MAX_THRESHOLD']),
                        str(PARAMS['START_TIME']),
                        str(PARAMS['TIME_INCREMENT'])+')'
                    ])
                )
            )

        # (iv) Output result
        with open(
            os.path.join(
                config['outputs']['path'],
                config['outputs']['root'],
                'results',
                'results.csv'
            ),
            'a'
        ) as file:
            file.write(
                ','.join([
                    '_'.join([
                        fileName,
                        str(solution['settings']['name'])
                    ]),
                    solution['settings']['type'],
                    str(PARAMS['MAX_THRESHOLD']),
                    str(PARAMS['START_TIME']),
                    str(PARAMS['TIME_INCREMENT']),
                    str(solution['stats']['rSq']),
                    str(solution['stats']['intercept']),
                    str(solution['stats']['slope']),
                    str(solution['stats']['threshold']),
                    str(solution['stats']['SSE']),
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


def fit_linear_regression(
    x,
    y
):
    """
    Variables
    ---------------------------------------------------------------------
    x                       = <list> Time series
    y                       = <list> Pressure series

    Description
    ---------------------------------------------------------------------
    Fits a linear regression model and returns the model attributes as
    a dictionary.
    """

    x = np.array([x]).reshape((-1, 1))
    y = np.array([y]).reshape((-1, 1))

    model = LinearRegression().fit(x, y)
    rSq = model.score(x, y)
    intercept = model.intercept_[0]
    slope = model.coef_[0][0]

    return {'rSq': rSq, 'intercept': intercept, 'slope': slope}


def pre_infusion_fitting_algorithm(
    solution,
    x,
    y,
    MAX_THRESHOLD=0.56,
    START_TIME=0,
    TIME_INCREMENT=0.8
):
    """
    Variables
    ---------------------------------------------------------------------
    solution                = <dict> Dictionary object
    x                       = <list> Time series
    y                       = <list> Pressure series
    MAX_THRESHOLD           = <int> Maximum slope threshold
                                that terminates the algorithm
    START_TIME              = <float> Indicates the start time of the
                                time series for fitting the linear
                                regression
    TIME_INCREMENT          = <float> Increment for each loop, shifting
                                the start of the time series

    Description
    ---------------------------------------------------------------------
    Evaluates whether an espresso extraction contains a pre-infusion
    period. If so, the algorithm returns a {solution}.
    """

    # Initialize local variables
    solution_ = {}
    threshold = None

    # Evaluate pre-infusion fit
    for end in list(range(1, 5)) + [max(x)]:

        solution_['stats'] = fit_linear_regression(
            x=x[x.index(START_TIME):(x.index(end)+1)],
            y=y[x.index(START_TIME):(x.index(end)+1)]
        )

        # If slope exceeds the maximum threshold, exit
        if abs(solution_['stats']['slope']) > MAX_THRESHOLD:
            threshold = solution_['stats']['slope']
            break

        # Update solution dictionary
        solution = {**solution, **solution_}
        solution['settings']['infusionDuration'] = end

        # Increment
        if end == 4:
            START_TIME = 0
        else:
            START_TIME = round(START_TIME + TIME_INCREMENT, 1)

    # Identify pre-infusion period
    if 'stats' not in solution.keys():
        solution['settings']['infusionDuration'] = 0
        solution['settings']['infusionPressure'] = 3
        solution['stats'] = {
            'rSq': None,
            'intercept': None,
            'slope': None
        }
    elif solution['settings']['infusionDuration'] == max(x):
        solution['settings']['infusionDuration'] = 0
        solution['settings']['infusionPressure'] = 3
    else:
        solution['settings']['infusionDuration'] = max(
            1,
            round(
                solution['settings']['infusionDuration'],
                0
            )
        )
        solution['settings']['infusionPressure'] = max(
            1,
            round(
                solution['stats']['intercept'],
                0
            )
        )

    # Retain slope that exceeded the maximum threshold
    solution['stats']['threshold'] = threshold

    return solution


def impute_pressure_nodes(
    solution,
    profile,
    smoothedProfileLst
):
    """
    Variables
    ---------------------------------------------------------------------
    solution                = <dict> Dictionary object of the fitted
                                solution
    profile                 = <dict> Dictionary object of the simulated
                                pressure profile
    smoothedProfileLst      = <list> List object containing the smoothed
                                pressure time series

    Description
    ---------------------------------------------------------------------
    Imputes the pressure profile nodes based on the {solution} and
    smoothed pressure time series and returns the quartiles.
    """

    # Determine start time of extraction
    if solution['settings']['infusionDuration'] == 0:
        profileMin = 0
    else:
        profileMin = int(
            solution['settings']['infusionDuration'] + 1
        )

    profileRange = list(
        np.arange(
            profileMin,
            float(solution['settings']['extractionDuration']),
            0.1
        )
    )

    # Calculate quartiles
    q0 = float(round(np.quantile(profileRange, 0), 1))
    q1 = float(round(np.quantile(profileRange, .25), 1))
    q2 = float(round(np.quantile(profileRange, .5), 1))
    q3 = float(round(np.quantile(profileRange, .75), 1))
    q4 = float(round(np.quantile(profileRange, 1), 1))

    # Lookup pressure values at each quartile
    solution['settings']['p0'] = (
        int(round(
            smoothedProfileLst[profile['settings']['timeLst'].index(q0)],
            0
        ))
    )
    solution['settings']['p1'] = (
        int(round(
            smoothedProfileLst[profile['settings']['timeLst'].index(q1)],
            0
        ))
    )
    solution['settings']['p2'] = (
        int(round(
            smoothedProfileLst[profile['settings']['timeLst'].index(q2)],
            0
        ))
    )
    solution['settings']['p3'] = (
        int(round(
            smoothedProfileLst[profile['settings']['timeLst'].index(q3)],
            0
        ))
    )
    solution['settings']['p4'] = (
        int(round(
            smoothedProfileLst[profile['settings']['timeLst'].index(q4)],
            0
        ))
    )

    return solution, [q0, q1, q2, q3, q4]


def calculate_sse(
    solution,
    profile
):
    """
    Variables
    ---------------------------------------------------------------------
    solution                = <dict> Dictionary object of the fitted
                                solution
    profile                 = <dict> Dictionary object of the simulated
                                pressure profile

    Description
    ---------------------------------------------------------------------
    Calculates the sum of squared error between the {profile} nodes and
    the {nodes} nodes.
    """

    # Evaluate the error
    if (
        profile['settings']['infusionDuration'] !=
        solution['settings']['infusionDuration']
    ):

        # Set error to na
        solution['stats']['SSE'] = np.nan

    else:

        # Calculate the error
        if solution['settings']['infusionDuration'] == 0:
            actual = np.array([
                profile['settings']['p0'],
                profile['settings']['p1'],
                profile['settings']['p2'],
                profile['settings']['p3'],
                profile['settings']['p4']
            ])
            fitted = np.array([
                solution['settings']['p0'],
                solution['settings']['p1'],
                solution['settings']['p2'],
                solution['settings']['p3'],
                solution['settings']['p4']
            ])
        else:
            actual = np.array([
                profile['settings']['infusionPressure'],
                profile['settings']['infusionPressure'],
                profile['settings']['p0'],
                profile['settings']['p1'],
                profile['settings']['p2'],
                profile['settings']['p3'],
                profile['settings']['p4']
            ])
            fitted = np.array([
                solution['settings']['infusionPressure'],
                solution['settings']['infusionPressure'],
                solution['settings']['p0'],
                solution['settings']['p1'],
                solution['settings']['p2'],
                solution['settings']['p3'],
                solution['settings']['p4']
            ])

        error = actual.ravel() - fitted.ravel()
        solution['stats']['SSE'] = np.dot(error, error)

    return solution


def plot_solution(
    solution,
    quartiles,
    fileName,
    scenario,
    paramLst
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
        scatterXLst = quartiles,
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
        ] + quartiles,
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
        0.92,
        'Sum of Squared Error: %s' % (
            round(solution['stats']['SSE'], 2)
        )
    )

    # Clear, format and plot profile values
    x1.clear()
    x1.set_ylabel(
        'Pressure'
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
            solution['settings']['pressureProfileLst']
            [:len(solution['settings']['timeLst'])]
        ),
        color='black',
        alpha=0.8,
        linewidth=1,
        label='Observed'
    )
    x1.plot(
        solution['settings']['timeLst'],
        (
            solution['settings']['smoothedProfileLst']
            [:len(solution['settings']['timeLst'])]
        ),
        color='black',
        alpha=0.4,
        linewidth=1,
        label='Smoothed'
    )
    x1.scatter(
        scatterXLst,
        scatterYLst,
        color='red',
        label='Solution',
        marker='o',
        s=50
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
                '_'.join([str(scenario), fileName, str(paramLst)]),
                'jpeg'
            ])
        )
    )
    plt.close('all')


def generate_output_directory(
    config
):
    """
    Variables
    ---------------------------------------------------------------------
    config                  = <dict> Dictionary object containing the
                                output directory structure

    Description
    ---------------------------------------------------------------------
    Recursively generates an output directory.
    """

    if 'outputs' in config.keys():

        # Create root output directory
        os.mkdir(
            os.path.join(
                config['outputs']['path'],
                config['outputs']['root']
            )
        )

        # Create output sub-directories
        if 'subFolders' in config['outputs'].keys():

            for folder in config['outputs']['subFolders']:
                os.mkdir(
                    os.path.join(
                        config['outputs']['path'],
                        config['outputs']['root'],
                        folder
                    )
                )

    else:
        raise KeyError(
            "ERROR: <config> does not contain the key, 'outputs'."
        )


def manage_results(
    config,
    fileName
):
    """
    Variables
    ---------------------------------------------------------------------
    fileName                = <str> Results file name

    Description
    ---------------------------------------------------------------------
    Removes {fileName} if it exists and re-creates it with the header
    row.
    """

    # Manage results
    if fileName in os.listdir(
        os.path.join(
            config['outputs']['path'],
            config['outputs']['root'],
            'results'
        )
    ):

        # Remove simulation results
        os.remove(
            os.path.join(
                config['outputs']['path'],
                config['outputs']['root'],
                'results',
                fileName
            )
        )

        # Create results header
        with open(
            os.path.join(
                config['outputs']['path'],
                config['outputs']['root'],
                'results',
                fileName
            ),
            'a'
        ) as file:
            file.write(
                ','.join([
                    'name',
                    'type',
                    'MAX_THRESHOLD',
                    'START_TIME',
                    'TIME_INCREMENT',
                    'r-sq',
                    'intercept',
                    'slope',
                    'threshold',
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

    else:

        # Create results header
        with open(
            os.path.join(
                config['outputs']['path'],
                config['outputs']['root'],
                'results',
                fileName
            ),
            'a'
        ) as file:
            file.write(
                ','.join([
                    'name',
                    'type',
                    'MAX_THRESHOLD',
                    'START_TIME',
                    'TIME_INCREMENT',
                    'r-sq',
                    'intercept',
                    'slope',
                    'threshold',
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


@utils.run_time
def retrieve_nan_solutions(
    dirName,
    fileName,
    paramsLst
):
    """
    Variables
    ---------------------------------------------------------------------
    dirName                 = <str> Directory path to solution dataset
    fileName                = <str> Results file name
    paramsLst               = <list> List of parameter combination lists

    Description
    ---------------------------------------------------------------------
    Retrieves a previously generated solutions dataset from {dirname} and
    returns a list of scenarios where the algorithm failed to fit a
    solution.
    """

    # Create parameter list dataframe
    paramsDf = pd.DataFrame(
        columns=[
            'MAX_THRESHOLD',
            'START_TIME',
            'TIME_INCREMENT'
        ]
    )
    for params in paramsLst:
        _paramsDf = pd.DataFrame(
            [params],
            columns=[
                'MAX_THRESHOLD',
                'START_TIME',
                'TIME_INCREMENT'
            ]
        )
        paramsDf = pd.concat(
            [paramsDf, _paramsDf],
            axis=0
        )

    # Import solutions
    solutionsDf = pd.read_csv(
        os.path.join(
            dirName,
            'results.csv'
        )
    )
    solutionsDf[
        ['file', 'id']
    ] = solutionsDf['name'].str.split(
        '_',
        expand=True
    )
    solutionsDf = solutionsDf[
        (solutionsDf['sse'].isnull()) &
        (solutionsDf['type'] == 'Solution') &
        (solutionsDf['file'] == fileName.split('.')[0])
    ]

    # Retrieve unique list of scenario IDs
    for col in [
        'MAX_THRESHOLD',
        'START_TIME',
        'TIME_INCREMENT'
    ]:
        paramsDf[col] = round(
            paramsDf[col].astype(float) * 100,
            0
        ).astype(int)
        solutionsDf[col] = round(
            solutionsDf[col].astype(float) * 100,
            0
        ).astype(int)

    scenarioDf = paramsDf.merge(
        solutionsDf[[
            'name',
            'MAX_THRESHOLD',
            'START_TIME',
            'TIME_INCREMENT',
            'id'
        ]],
        how='inner',
        validate='1:m'
    )
    scenarioDf = scenarioDf[['id']].drop_duplicates().reset_index(drop=True)

    return scenarioDf['id'].to_list()


if __name__ == '__main__':

    # Initialize global variables
    simulate = True
    solve = True
    plot = True
    retrieve = True
    source = '2023-07-25 07-20-31PM'
    seed = 1
    n = 'FULL_SAMPLE'
    config = {
        "outputs": {
            'path': os.path.join(
                os.path.join(os.path.dirname(__file__), os.pardir),
                'simulation'
            ),
            'root': datetime.datetime.now().strftime("%Y-%m-%d %I-%M-%S%p"),
            'subFolders': ['config', 'plots', 'results']
        }
    }

    # Initialize profile simulation variables
    infusionDurationLst = [0, 3]
    infusionPressureLst = [1, 3, 6]
    extractionDurationLst = [15, 25]
    extractionPressureLst = [6, 7, 9]

    # Initialize pressure fitting algorithm variables
    maxThresholdLst = [
        round(item, 2) for item in list(np.arange(0.4, 0.6, 0.01))
    ]
    startTimeLst = [
        round(item, 1) for item in list(np.arange(0.0, 0.4, 0.1))
    ]
    timeIncrementLst = [
        round(item, 1) for item in list(np.arange(0.5, 1.1, 0.1))
    ]

    # Assign seed for random sample
    random.seed(seed)

    # Generate output directory
    generate_output_directory(
        config=config
    )

    # Manage results outputs
    manage_results(
        config=config,
        fileName='results.csv'
    )

    # Simulate pressure profiles
    if simulate:

        # Generate list of scenarios to simulate
        scenarioLst = []

        for infusionDuration in infusionDurationLst:
            if infusionDuration == 0:
                scenarioLst = scenarioLst + [
                    combination for combination in itertools.product(*[
                        extractionDurationLst,
                        [infusionDuration],
                        [3],
                        extractionPressureLst,
                        extractionPressureLst,
                        extractionPressureLst,
                        extractionPressureLst,
                        extractionPressureLst
                    ])
                ]
            else:
                scenarioLst = scenarioLst + [
                    combination for combination in itertools.product(*[
                        extractionDurationLst,
                        [infusionDuration],
                        infusionPressureLst,
                        extractionPressureLst,
                        extractionPressureLst,
                        extractionPressureLst,
                        extractionPressureLst,
                        extractionPressureLst
                    ])
                ]

        # Simulate
        simulate_pressure_profiles(
            config=config,
            scenarioLst=scenarioLst,
            fileName='simulated.json'
        )

    else:

        # Retrieve diagnostic results
        pass

    '''
    Sample scenarios
    ----------------

      No    pre-infusion,
        scenarioLst=['192', '16383'],
        fileName='Profiles_0 Pre-Infusion'

      Short pre-infusion,
        scenarioLst=['50067', '79980'],
        fileName='Profiles_1 Pre-Infusion'

      Long  pre-infusion,
        scenarioLst=['6560, 62432'],
        fileName='Profiles_3 Pre-Infusion'

    Example
    -------

    fit_pressure_profile(
        config=utils.read_config(
            configLoc=os.path.join(
                os.path.join(os.path.dirname(__file__), os.pardir),
                'simulation',
                'config',
                'Profiles_0 Pre-Infusion.json'
            )
        ),
        scenarioLst=['192'],
        fileName=('Profiles_0 Pre-Infusion.json').split('.')[0],
        plot=plot,
        PARAMS=PARAMS
    )
    '''

    # Evaluate scenarios
    if solve:

        # Iterate over algorithm config

        '''
        Full parameter matrix
        ---------------------
        [
            combination for combination in itertools.product(*[
                maxThresholdLst,
                startTimeLst,
                timeIncrementLst,
                maxDifferenceLst
            ])
        ]

        Optimal parameter matrix
        ------------------------
        paramsLst = [
            [0.45, 0, 0.8]
        ]

        Top 20 Optimal parameter matrix (least unsolved)
        ------------------------------------------------

        paramsLst = [
            [0.56, 0, 0.8, 0.3],
            [0.54, 0, 0.8],
            [0.5, 0, 0.7],
            [0.51, 0, 0.7],
            [0.55, 0, 0.8],
            [0.51, 0, 0.8],
            [0.52, 0, 0.8],
            [0.45, 0, 0.7],
            [0.5, 0, 0.8],
            [0.47, 0, 0.7],
            [0.53, 0, 0.8],
            [0.45, 0, 0.8],
            [0.5, 0.1, 0.7],
            [0.56, 0.1, 0.7],
            [0.51, 0.1, 0.7],
            [0.54, 0.1, 0.7],
            [0.43, 0, 0.8],
            [0.55, 0.1, 0.7],
            [0.41, 0, 0.6],
            [0.42, 0, 0.7],
        ]
        '''

        # Initialize params list
        # paramsLst = [
        #     combination for combination in itertools.product(*[
        #         maxThresholdLst,
        #         startTimeLst,
        #         timeIncrementLst
        #     ])
        # ]
        paramsLst = [
            [0.42, 0.0, 0.8]
        ]
        print('\n')
        print('Solving %s parameter combinations' % len(paramsLst))

        # Evaluate scenarios
        for fileName in os.listdir(
            os.path.join(
                config['outputs']['path'],
                config['outputs']['root'],
                'config'
            )
        ):

            # Read config
            profiles = utils.read_config(
                configLoc=os.path.join(
                    config['outputs']['path'],
                    config['outputs']['root'],
                    'config',
                    fileName
                )
            )

            # Create scenario list
            if retrieve:
                scenarioLst = retrieve_nan_solutions(
                    dirName=os.path.join(
                        config['outputs']['path'],
                        source,
                        'results'
                    ),
                    fileName=fileName,
                    paramsLst=paramsLst
                )

            else:
                if n == 'FULL_SAMPLE':
                    scenarioLst = list(profiles.keys())

                else:
                    scenarioLst = random.sample(
                        list(profiles.keys()),
                        n
                    )

            for item in paramsLst:

                # Construct profile fitting parameters
                PARAMS = {
                    'MAX_THRESHOLD': item[0],
                    'START_TIME': item[1],
                    'TIME_INCREMENT': item[2]
                }
                print('\n')
                print(str(PARAMS))

                # Fit pressure profile
                fit_pressure_profile(
                    config=config,
                    profiles=profiles,
                    scenarioLst=scenarioLst,
                    fileName=fileName.split('.')[0],
                    plot=plot,
                    PARAMS=PARAMS
                )

    # Summarize diagnostics
    df = pd.read_csv(
        os.path.join(
            config['outputs']['path'],
            config['outputs']['root'],
            'results',
            'results.csv'
        ),
        sep=','
    )
    df['n'] = n

    summaryDf = df.groupby(
        [
            'MAX_THRESHOLD',
            'START_TIME',
            'TIME_INCREMENT',
            'n',
            'sse'
        ],
        dropna=False
    ).agg(
        count=('name', 'count')
    ).reset_index()
    totalDf = summaryDf.groupby(
        [
            'MAX_THRESHOLD',
            'START_TIME',
            'TIME_INCREMENT',
            'n',
        ],
        dropna=False
    ).agg(
        total=('count', 'sum')
    ).reset_index()
    diagnosticDf = summaryDf.merge(
        totalDf,
        how='left',
        validate='m:1'
    )
    diagnosticDf['percent'] = (
        diagnosticDf['count'] / diagnosticDf['total']
    )
    diagnosticDf['sse'] = diagnosticDf['sse'].fillna('nan')

    # Output diagnostic results
    diagnosticDf.to_csv(
        os.path.join(
            config['outputs']['path'],
            config['outputs']['root'],
            'results',
            'diagnostics.csv'
        ),
        sep=',',
        index=False
    )
