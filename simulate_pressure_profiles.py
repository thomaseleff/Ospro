"""
Information
---------------------------------------------------------------------
Name        : simulate_pressure_profiles.py
Location    : ~/
Author      : Tom Eleff
Published   : 2023-09-03
Revised on  : ~

Description
---------------------------------------------------------------------
Simulates espresso pressure profiles.
"""

# Import modules
import os
import time
import datetime as dt
import pandas as pd
import ospro.utils.utils as utils
from ospro.algorithms.espresso_profile_fitting_algorithm import EPFA as EPFA

# Run simulations
if __name__ == '__main__':

    # Initialize global variables
    dirName = os.path.join(
        os.path.dirname(__file__),
        'diagnostics'
    )
    config = {
        'outputs': {
            'path': os.path.join(
                os.path.dirname(__file__),
                'simulation'
            ),
            'root': dt.datetime.now().strftime("%Y-%m-%d %I-%M-%S%p"),
            'subFolders': ['plots', 'results', 'profiles']
        }
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

            # Import extraction data series
            df = pd.read_csv(
                os.path.join(dirName, file),
                sep=','
            )
            x = df['Duration'].to_numpy()
            y = df['Pressure'].to_numpy()

            # Initialize the espresso profile fitting algorithm
            epfa = EPFA()

            # Call the espresso profile fitting algorithm
            t1 = time.time()
            solution = epfa.solve(x=x, y=y)
            t2 = time.time()
            td = dt.timedelta(seconds=(t2-t1))

            # Preserve execution time
            solution['ppfa']['runTime'] = ' '.join([
                str(td),
                'hh:mm:ss'
            ])

            # Plot
            epfa.plot_solution(
                solution=solution,
                dirName=os.path.join(
                    config['outputs']['path'],
                    config['outputs']['root'],
                    'plots'
                ),
                fileName=file.split('.')[0]
            )

            # Output profile
            utils.write_config(
                configLoc=os.path.join(
                    config['outputs']['path'],
                    config['outputs']['root'],
                    'profiles',
                    '.'.join([
                        '_'.join(['epfa', str(solution['ppfa']['id'])]),
                        'json'
                    ])
                ),
                config=solution
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
                        str(solution['ppfa']['runTime']),
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
                    len2=40
                )
            )
