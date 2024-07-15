"""
Information
---------------------------------------------------------------------
Name        : espresso_profile_fitting_algorithm.py
Location    : ~/ospro/algorithms

Description
---------------------------------------------------------------------
Identifies the espresso profile settings based on an espresso
extraction time-series.
"""

# Import modules
import os
import scipy
import numpy as np
import matplotlib.pyplot as plt
from numpy.core.multiarray import interp as compiled_interp


# Define pressure profile fitting algorithm class
class EPFA():

    def __init__(
        self,
        TIME_INTERVAL=0.1,
        START_DELAY=1,
        EXTRACTION_DURATION_MIN=10,
        INFUSION_DURATION_LIMIT=30,
        INFUSION_LIMIT=4
    ):
        """
        Variables
        ---------------------------------------------------------------------
        TIME_INTERVAL           =  <float> Interval of the time series
                                        (seconds)
        START_DELAY             =  <int> Period of duration in time (seconds)
                                        to omit from the expresso extraction
                                        time-series.
        EXTRACTION_DURATION_MIN =  <int> Minimum period of duration in time
                                        (seconds) for an espresso extraction
                                        to have pre-infusion.
        INFUSION_DURATION_LIMIT =  <int> Maximum period of duration in time
                                        (seconds) for pre-infusion.
        INFUSION_LIMIT          =  <int> Maximum pressure (bars) for
                                        pre-infusion.

        Description
        ---------------------------------------------------------------------
        Initializes an instance of the espresso profile fitting algorithm.
        """

        # Assign algorithm parameters
        self.TIME_INTERVAL = TIME_INTERVAL
        self.START_DELAY = START_DELAY
        self.EXTRACTION_DURATION_MIN = EXTRACTION_DURATION_MIN
        self.INFUSION_DURATION_LIMIT = INFUSION_DURATION_LIMIT
        self.INFUSION_LIMIT = INFUSION_LIMIT
        self.TIME_INTERVAL_CONVERSION = np.round(
            1 / TIME_INTERVAL, decimals=0
        ).astype(int)

    def solve(
        self,
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
        Performs an OLS algorithm that determines the best fitted
        pressure profile from espresso extraction time series
        data.
        """

        # Determine the possible local infusion and extraction
        #   pressure values
        xti, ypi, yp0, yp1, yp2, yp3, yp4, ysmoothed = self.reduce(x=x, y=y)

        # Simulate the possible espresso extraction profiles
        maty0, profiles = self.simulate_profiles(
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
        solution = self.fit_profile(
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
            infusionPressure = 0
            p0, p1, p2, p3, p4 = (
                profiles[solution['id']]
            )

        return {
            'settings': {
                'name': 'User_1',
                'type': 'User',
                'extractionDuration': float(x[-1]),
                'infusionDuration': int(infusionDuration),
                'infusionPressure': int(infusionPressure),
                'p0': int(p0),
                'p1': int(p1),
                'p2': int(p2),
                'p3': int(p3),
                'p4': int(p4),
                'timeLst': x.tolist(),
                'pressureProfileLst': np.round(
                    maty0[solution['id']],
                    1
                ).tolist(),
                'pressureSeries': y.tolist(),
                'pressureSeriesSmoothed': ysmoothed.tolist()
            },
            'ppfa': solution
        }

    def reduce(
        self,
        x,
        y
    ):
        """
        Variables
        ---------------------------------------------------------------------
        x                       = <np.array()> Vector of the Time series
        y                       = <np.array()> Vector of the Pressure series
        START_DELAY             = <int> Period of duration in time (seconds)
                                    to omit from the expresso extraction
                                    time-series.
        INFUSION_DURATION_LIMIT = <int> Maximum period of duration in
                                    time (seconds) for pre-infusion.
        INFUSION_LIMIT          = <int> Maximum pressure (bars)
                                    considered to be pre-infusion.

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

        # Determine the first index where pressure exceeds
        #   the pre-infusion pressure limit
        INFUSION_DURATION_INDEX = np.round(
            np.argmax(
                ysmoothed[
                    np.round(
                        self.START_DELAY * self.TIME_INTERVAL_CONVERSION,
                        decimals=0
                    ):
                ] >= self.INFUSION_LIMIT
            ) + np.round(
                self.START_DELAY * self.TIME_INTERVAL_CONVERSION,
                decimals=0
            ),
            decimals=0
        )

        # Evaluate pre-infusion
        if (
            (
                ysmoothed.shape[0] >= np.round(
                    (
                        self.EXTRACTION_DURATION_MIN *
                        self.TIME_INTERVAL_CONVERSION
                    ),
                    decimals=0
                )
            ) and
            (
                INFUSION_DURATION_INDEX > np.round(
                    self.START_DELAY * self.TIME_INTERVAL_CONVERSION,
                    decimals=0
                )
            )
        ):

            # Derive pre-infusion duration values
            xti = self.reduce_range(
                a=x[
                    np.round(
                        (
                            INFUSION_DURATION_INDEX -
                            self.TIME_INTERVAL_CONVERSION
                        ),
                        decimals=0
                    ):INFUSION_DURATION_INDEX
                ]
            )

            # Derive local extraction pressure values
            ypi = self.reduce_range(a=ysmoothed[:np.where(x == xti[-1])[0][0]])
            yp0, yp1, yp2, yp3, yp4 = (
                self.derive_local_extraction_pressure_ranges(
                    x=x,
                    y=ysmoothed,
                    xti=xti
                )
            )
            yp0 = self.reduce_range(a=yp0)
            yp1 = self.reduce_range(a=yp1)
            yp2 = self.reduce_range(a=yp2)
            yp3 = self.reduce_range(a=yp3)
            yp4 = self.reduce_range(a=yp4)

        else:

            # Derive pre-infusion duration values
            xti = np.array([0])

            # Derive local extraction pressure values
            ypi = np.array([])
            yp0, yp1, yp2, yp3, yp4 = (
                self.derive_local_extraction_pressure_ranges(
                    x=x,
                    y=ysmoothed,
                    xti=xti
                )
            )
            yp0 = self.reduce_range(a=yp0)
            yp1 = self.reduce_range(a=yp1)
            yp2 = self.reduce_range(a=yp2)
            yp3 = self.reduce_range(a=yp3)
            yp4 = self.reduce_range(a=yp4)

        # Return local pressure values
        return xti, ypi, yp0, yp1, yp2, yp3, yp4, ysmoothed

    def derive_local_extraction_pressure_ranges(
        self,
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
        self,
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
            start=np.floor(np.max(np.array([np.min(a), 1]))),
            stop=np.round(
                np.ceil(np.max(a) + 1),
                decimals=0
            ),
            step=1
        )

    def simulate_profiles(
        self,
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
                        func1d=self.interpolate,
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
                        func1d=self.interpolate,
                        axis=1,
                        arr=sextraction,
                        x=x
                    )
                ),
                axis=0
            )

        return maty0, profiles

    def interpolate(
        self,
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
        #   xp = np.array([
        #       0,
        #       {inf. dur},
        #       {t0},
        #       {t1},
        #       {t2},
        #       {t3},
        #       {t4}
        #   ])
        #   fp = np.array([
        #       {inf. pres},
        #       {inf. pres},
        #       {p0},
        #       {p1},
        #       {p2},
        #       {p3},
        #       {p4}
        #   ])
        if a.shape[0] > 5:
            xp = np.concatenate(
                (
                    np.array([0, a[0]]),
                    np.array(self.calculate_quartiles(
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
        #   xp = np.array([
        #       {t0},
        #       {t1},
        #       {t2},
        #       {t3},
        #       {t4}
        #   ])
        #   fp = np.array([
        #       {p0},
        #       {p1},
        #       {p2},
        #       {p3},
        #       {p4}
        #   ])
        else:
            xp = self.calculate_quartiles(
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
        self,
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

        # Derive the start time from the simulated espresso extraction
        #   parameters
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
        self,
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
            'id': int(id),
            'sse': float(np.round(sse[id], 6)),
            'simulations': int(sse.shape[0])
        }

    def plot_solution(
        self,
        solution,
        dirName,
        fileName
    ):
        """
        Variables
        ---------------------------------------------------------------------
        solution                = <dict> Dictionary object of the fitted
                                    solution
        dirName                 = <str> Output directory path
        fileName                = <str> Prefix for the plot file name

        Description
        ---------------------------------------------------------------------
        Imputes the pressure profile nodes based on the {solution} and
        smoothed pressure time series and returns the quartiles.
        """

        # Unpack the solution
        if solution['settings']['infusionDuration'] == 0:
            scatterXLst = self.calculate_quartiles(
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
            ] + self.calculate_quartiles(
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

        # Create the plot figure
        fig = plt.figure()
        x1 = fig.add_subplot(1, 1, 1)
        plt.figtext(
            0.15,
            0.95,
            'Run-time: %s' % (
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
                dirName,
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
