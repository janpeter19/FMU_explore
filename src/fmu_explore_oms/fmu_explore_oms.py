"""Explain the module"""

# module fmu_explore_oms
# Author: Jan Peter Axelsson
# License:  GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007
# ------------------------------------------------------------------------------------------------------------------
# 2026-09-26 - Created from a script-version 1.0.3 date 2026-03-26 with origin long time back, presnte 2022-01-31
# ------------------------------------------------------------------------------------------------------------------

import platform
import zipfile
from itertools import cycle
from importlib_metadata import version, PackageNotFoundError

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as img
import pandas as pd




def empty_function(*args, **kwargs):
    """Just an empty function to handle external_function as argument for the class."""

    return None


class AdaptWith:
    """The class parameters essentially adapt the functions to the
    context of the application."""

    # Set the actual variables associated with the application given
    def __init__(
        self,
        parValue,
        parLocation,
        parCheck,
        model,
        fmu_model,
        fmu_process_diagram,
        MSL_usage,
        MSL_version,
        BPL_version,
        options,
        simulationTime,
        timeDiscreteStates,
        diagrams,
        ax,
        lines,
        external_function=empty_function,
    ):

        # Define self variables
        self.parValue = parValue
        self.parLocation = parLocation
        self.parCheck = parCheck
        self.model = model
        self.fmu_model = fmu_model
        self.fmu_process_diagram = fmu_process_diagram
        self.MSL_usage = MSL_usage
        self.MSL_version = MSL_version
        self.BPL_version = BPL_version
        self.options = options
        self.simulationTime = simulationTime
        self.timeDiscreteStates = timeDiscreteStates
        self.diagrams = diagrams
        self.ax = ax
        self.lines = lines
        self.external_function = external_function
        self.sim_res = None
        self.t = None
        self.prevFinalTime = 0

        # Create stateValue that later will be used to store final state
        # and used for initialization in 'cont'


    # ---------------------------------------------------------------------------------------------

    def readParValue(self, file, sheet):
        """Read parameter short names and values from an Excel-file from 
        defined sheet. For use in the notebook! Return a dictionary."""

        parValue = self.parValue

        parValue_local = {}
        table = pd.ExcelFile(file).parse(sheet)
        for k in list(range(len(table))):
            parValue_local[table["Par"][k]] = table["Value"][k]
        parValue.update(parValue_local)


    def readParLocation(self, file, sheets):
        """Read parameter short and long names from an Excel-file sheet by sheet. 
        For use in the notebook! Return a dictionary."""

        parLocation = self.parLocation

        parLocation_local = {}
        for sheet in sheets:
            table = pd.ExcelFile(file).parse(sheet)
            for k in list(range(len(table))):
                parLocation_local[table["Par"][k]] = table["Location"][k]
        parLocation.update(parLocation_local)


    def par(self, *x, **x_kwarg):
        """Set parameter values if available in the predefined dictionary parValue."""

        parValue = self.parValue
        parCheck = self.parCheck

        x_kwarg.update(*x)
        x_temp = {}

        for key in x_kwarg:
            if key in parValue:
                x_temp.update({key: x_kwarg[key]})
            else:
                print(
                    "Error:",
                    key,
                    "- seems not an accessible parameter - check the spelling",
                )
        parValue.update(x_temp)

        parErrors = [requirement for requirement in parCheck if not eval(requirement)]
        if not parErrors == []:
            print("Error - the following requirements do not hold:")
            for item in enumerate(parErrors):
                print(item)


    def init(self, *x, **x_kwarg):
        """Set initial values of the state variables. The name should contain string '_start' 
        to be accepted. The function can handle general parameter string location names 
        if entered as a dictionary."""

        parValue = self.parValue

        x_kwarg.update(*x)
        x_init = {}

        for key in x_kwarg:
            if "_start" in key:
                x_init.update({key: x_kwarg[key]})
            else:
                print(
                    "Error:",
                    key,
                    "- seems not an initial value, use par() instead - check the spelling",
                )
        parValue.update(x_init)





    def setPen(self, lines_new):
        """Set the list of maximally four pens for the diagram."""

        self.lines = lines_new


    def resetPen(self):
        """Set the pen to the first one in the list."""

        self.linecycler = cycle(self.lines)


    def show(self):
        """Show diagrams chosen by newplot() and stored in sim_res last simulation."""

        diagrams = self.diagrams
        ax = self.ax
        linecycler = self.linecycler
        t = self.t
        sim_res = self.sim_res
        external_function = self.external_function

        # Plot pen
        linetype = next(linecycler)

        # Plot diagrams
        context = locals().copy()
        context[self.external_function.__name__] = self.external_function
        for command in diagrams:
            eval(command, {}, context)





    def describe_MSL(self):
        """List MSL version and components used."""

        MSL_usage = self.MSL_usage

        print("MSL:", MSL_usage)





    def process_diagram(self):
        """Plot the process diagram."""

        fmu_model = self.fmu_model
        fmu_process_diagram = self.fmu_process_diagram

        try:
            process_diagram = zipfile.ZipFile(fmu_model, "r").open(
                "documentation/processDiagram.png"
            )
        except KeyError:
            print("No processDiagram.png file in the FMU, but try the file on disk.")
            process_diagram = fmu_process_diagram
        try:
            plt.imshow(img.imread(process_diagram))
            plt.axis("off")
            plt.show()
        except FileNotFoundError:
            print("And no such file on disk either")


    def FMU_explore_info(self):
        """Describe briefly teh FMU_explore commands."""

        print()
        print("Model for the process has been setup. Key commands:")
        print(" - par()       - change of parameters and initial values")
        print(" - init()      - change initial values only")
        print(" - simu()      - simulate and plot")
        print(" - newplot()   - make a new plot")
        print(" - show()      - show plot from previous simulation")
        print(
            " - disp()      - display parameters and initial values from the last simulation"
        )
        print(
            " - describe()  - describe culture, broth, parameters, variables with values/units"
        )
        print()
        print(
            "Note that both disp() and describe() takes values from the last simulation"
        )
        print("and the command process_diagram() brings up the main configuration")
        print()
        print("Brief information about a command by help(), eg help(simu)")
        print("Key system information is listed with the command system_info()")


    def system_info(self):
        """Describe system information."""

        model = self.model
        MSL_version = self.MSL_version
        BPL_version = self.BPL_version

        FMU_type = model.__class__.__name__
        print()
        print("System information")
        print(" -OS:", platform.system())
        print(" -Python:", platform.python_version())
        try:
            print(" -Scipy:", version("scipy"))
        except PackageNotFoundError:
            print(" -Scipy: not installed in the notebook")
        print(" -OMSimulator:")
        print(" -FMU by:", model.get_generation_tool())
        print(" -FMI:", model.get_version())
        print(" -Type:", FMU_type)
        print(" -Name:", model.get_name())
        print(" -Generated:", model.get_generation_date_and_time())
        print(" -MSL:", MSL_version)
        print(" -Description:", BPL_version)
        print(" -Interaction: FMU_explore version", version("FMU_explore"))


    def SDG(self, explanation=False):
        """Acknowledgement. Explanation of the SDG and its history."""

        if explanation:
            print('"Soli Deo Gloria"')
            print(' It is latin and means "To the honour of God".')
            print(" The great composer Johan Sebastian Bach",
                  " used to end his compositions with this small remark SDG.")
            print(" And I like to do that too :).")
