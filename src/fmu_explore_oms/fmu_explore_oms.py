"""The module provide a simplified interaction with OMSimulator useful for Jupyter notebook"""

# Module: fmu_explore_oms
# Author: Jan Peter Axelsson
# License:  GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007
# ------------------------------------------------------------------------------------------------------------------
# 2026-09-26 - Created from a script-version 1.0.3 date 2026-03-26 with origin long time back, presented 2022-01-31
# 2026-09-30 - A first rudimentary version of the module with functions: par(), init(), simu(), show()
# 2026-10-06 - Added options as a parameter
# 2026-10-07 - Handle sim_res file with DyMat
# 2026-10-07 - Make use of model.reset() introduced in ver 3.0.0.post198 released today
# 2026-10-08 - Added function disp() from pyfmi and just replacedted get() with getValue() - need reset() first!
# 2026-10-09 - Fix simu() with proper reset-handling
# 2026-10-24 - Role back simu() to v1.2.6 
# 2026-11-05 - New structure of simu() and avoid terminate() and delete to enable acess to model after simu()
# 2026-11-06 - Added function model_get to harmonize notebooks
# 2026-11-07 - Added external_function usage
# 2026-11-09 - Added code for handling simu('cont')
# 2026-11-10 - Added code to initially make stateValue dictionary 
# ------------------------------------------------------------------------------------------------------------------

import platform
import zipfile
from itertools import cycle
from importlib_metadata import version, PackageNotFoundError

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as img
import pandas as pd

import OMSimulator as oms
import scipy.io
import DyMat


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

        # Create the model
        self.model = oms.FMU(self.fmu_model)

        # Create stateValue that later will be used to store final state
        # and used for initialization in 'cont'
        stateValue = {}
        # More OMS code here...
        stateValue.update(self.timeDiscreteStates)
        self.stateValue = stateValue

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


    def model_get(self, parLoc):
        """Function corresponds to pyfmi model.get() but returns just a value and not a list"""
        
        value = self.model.getValue(parLoc)
        return value

    def disp(self, name="", decimals=3, mode="short"):
        """Display intial values and parameters in the model that include "name" and 
        is in parLocation list. Note, it does not take the value from the dictionary par 
        but from the model."""

        model = self.model
        parValue = self.parValue
        parLocation = self.parLocation

        def dict_reverser(d):
            """Simply reverse the dictionary. A help function."""

            seen = set()
            return {v: k for k, v in d.items() if v not in seen or seen.add(v)}

        if mode in ["short"]:
            k = 0
            for Location in [parLocation[k] for k in parValue.keys()]:
                if name in Location:
                    if not isinstance(model.getValue(Location), np.bool_):
                        print(
                            dict_reverser(parLocation)[Location],
                            ":",
                            np.round(model.getValue(Location), decimals),
                        )
                    else:
                        print(
                            dict_reverser(parLocation)[Location],
                            ":",
                            model.getValue(Location),
                        )
                else:
                    k = k + 1
            if k == len(parLocation):
                for parName in parValue.keys():
                    if name in parName:
                        if not isinstance(model.getValue(Location), np.bool_):
                            print(
                                parName,
                                ":",
                                np.round(model.getValue(parLocation[parName]), decimals),
                            )
                        else:
                            print(parName, ":", model.getValue(parLocation[parName]))
        if mode in ["long", "location"]:
            k = 0
            for Location in [parLocation[k] for k in parValue.keys()]:
                if name in Location:
                    if not isinstance(model.getValue(Location), np.bool_):
                        print(
                            Location,
                            ":",
                            dict_reverser(parLocation)[Location],
                            ":",
                            np.round(model.getValue(Location), decimals),
                        )
                else:
                    k = k + 1
            if k == len(parLocation):
                for parName in parValue.keys():
                    if name in parName:
                        if not isinstance(model.getValue(Location), np.bool_):
                            print(
                                parLocation[parName],
                                ":",
                                dict_reverser(parLocation)[Location],
                                ":",
                                parName,
                                ":",
                                np.round(model.getValue(parLocation[parName]), decimals),
                            )


    def restart(self):
        """Restart the model"""

        self.model = oms.FMU(self.fmu_model)
        self.model.instantiate()


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


    def simu(self, simulationTime=None, mode="Initial", options=None):
        """Simulation of model and plot of results.T he given intial values and parameters are given in parValue 
        and given before. The plot window is also setup before."""

        parValue = self.parValue

        parLocation = self.parLocation

        stateValue = self.stateValue

        prevFinalTime = self.prevFinalTime

        fmu_model = self.fmu_model

        if simulationTime is None:
            simulationTime = self.simulationTime

        if options is None:
            options = self.options

        diagrams = self.diagrams
        ax = self.ax
        linecycler = self.linecycler

        external_function = self.external_function

        # Simulation flag
        simulationDone = False

        # Prepare for simulation
        if hasattr(self, 'model') and self.model is not None:
            try:
                self.model.delete()
            except Exception:
                pass

        self.model = oms.FMU(fmu_model)
        self.model.instantiate()

        # Set options for the result file and more
        self.model.setResultFile('sim_res.mat')
        if options is not None:
            for command in options: 
                eval(command)

        # Run simulation
        if mode in ["Initial", "initial", "init"]:

            # Set parameters and initial values:
            for key in parValue.keys():
                self.model.setValue(parLocation[key], parValue[key])
            self.model.setStopTime(simulationTime)

            # Simulate
            self.model.initialize()
            self.model.simulate()
            simulationDone = True
            
            # Store results to the class
            temp = scipy.io.loadmat('sim_res.mat')
            t = temp['data_2'][0]
            sim_res = DyMat.DyMatFile('sim_res.mat')
            self.t = t
            self.sim_res = sim_res

        elif mode in ["Continued", "continued", "cont"]:

            if prevFinalTime == 0:
                print("Error: Simulation is first done with default mode = init'")
            else:

                # Set parameters and intial state values:
                for key in parValue.keys():
                    self.model.setValue(parLocation[key], parValue[key])

                for key in stateValue.keys():
                    if not key[-1] == "]":
                        if key[-3:] == "I.y":
                            self.model.setValue(key[:-10] + "I_start", stateValue[key])
                        elif key[-3:] == "D.x":
                            self.model.setValue(key[:-10] + "D_start", stateValue[key])
                        else:
                            self.model.setValue(key + "_start", stateValue[key])
                    elif key[-3] == "[":
                        self.model.setValue(key[:-3] + "_start" + key[-3:], stateValue[key])
                    elif key[-4] == "[":
                        self.model.setValue(key[:-4] + "_start" + key[-4:], stateValue[key])
                    elif key[-5] == "[":
                        self.model.setValue(key[:-5] + "_start" + key[-5:], stateValue[key])
                    else:
                        print("The state vecotr has more than 1000 states")
                        break

                # Set simulation time
                self.model.setStartTime = prevFinalTime
                self.model.setStopTime = prevFinalTime + simulationTime
                
                #print('StartTime -cont', prevFinalTime)
                #print('StopTime -cont', simulationTime)

                # Simulate
                self.model.initialize()
                self.model.simulate()
                simulationDone = True

                # Store results to the class
                temp = scipy.io.loadmat('sim_res.mat')
                t = temp['data_2'][0]
                sim_res = DyMat.DyMatFile('sim_res.mat')
                self.t = t
                self.sim_res = sim_res

        else:
            print("Simulation mode not correct")

        if simulationDone:

            # Plot results
            linetype = next(linecycler)
            context = locals().copy()
            context[self.external_function.__name__] = self.external_function

            for command in diagrams:
                eval(command, {}, context)

            # Store final state values stateValue:
            for key in list(stateValue.keys()):
                stateValue[key] = self.model.getValue(key)

            # Store time from where simulation will start next time
            self.prevFinalTime = t[-1]
            
            #print('Next prevFinalTime', t[-1])

        else:
            print("Error: No simulation done")

    def describe_MSL(self):
        """List MSL version and components used."""

        MSL_usage = self.MSL_usage

        print("MSL:", MSL_usage)


    def describe_general(self, name, decimals):
        """Describe time, process, parameters and variables in the Modelica code."""

        parLocation = self.parLocation
        model = self.model

        if name == "time":
            description = "Time"
            unit = "h"
            print(description, "[", unit, "]")

        elif name == "process":
            print(model.description)


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
        print(" -OMSimulator:", oms.__version__)
        print(" -FMU by:", self.model.generationTool)
        print(" -FMI:", self.model.fmiVersion)
        print(" -Type:", self.model.fmuType)
        print(" -Name:", self.model.modelName)
        print(" -Generated:", self.model.generationDateAndTime)
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
