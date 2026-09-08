# module fmu_explore_fmpy
# Author: Jan Peter Axelsson
# License:  GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007
#------------------------------------------------------------------------------------------------------------------
# 2026-09-02 - Created - start from fmu_explore_pyfmi ver 1.1.4 and now call it ver 1.1.5
# 2026-09-03 - Changed to model_description, corrected arguments for functions
# 2026-09-04 - Fixes of model_get etc, disp(), describe_general(), while simu() remains to be fixed also model_get
# 2026-09-07 - Another fix of disp() and a couple of fixes for model_get - self.sim_res and self_start_values
# 2026-09-08 - Fixed a model.get... to model_get... in describe_general()
#------------------------------------------------------------------------------------------------------------------

import sys
import platform
import numpy as np 
import matplotlib.pyplot as plt 
import matplotlib.image as img
import pandas as pd
import zipfile
from importlib_metadata import version 
from fmpy import simulate_fmu
from fmpy import read_model_description
import fmpy as fmpy
from itertools import cycle

def empty_function(*args, **kwargs):
   return None

class fmu_explore:
      
   # Set the actual variables associated with the application given
   def __init__(self, model, parValue, parLocation, parCheck, fmu_model, fmu_process_diagram, \
                      MSL_usage, MSL_version, BPL_version, \
                      options, simulationTime, timeDiscreteStates, stateValue, stateValueInitial, stateValueInitialLoc, keyVariables, \
                      diagrams, ax, lines, \
                      external_function=empty_function):
                     
      self.FMU_explore_version = 'FMU-explore version 1.1.6'
      self.model_description = model
      self.parValue = parValue  
      self.parLocation = parLocation
      self.parCheck = parCheck
      self.MSL_usage = MSL_usage
      self.MSL_version = MSL_version
      self.BPL_version = BPL_version
      self.fmu_model = fmu_model
      self.fmu_process_diagram = fmu_process_diagram
      self.options = options
      self.simulationTime = simulationTime                                    
      self.timeDiscreteStates = timeDiscreteStates
      self.stateValue = stateValue
      self.stateValueInitial = stateValueInitial
      self.stateValueInitialLoc = stateValueInitialLoc
      self.keyVariables = keyVariables
      self.diagrams = diagrams     
      self.ax = ax                 
      self.lines = lines
      self.external_function = external_function
      self.start_values = None
      self.sim_res = None
      self.t = None

   # Define how to read dictionary for parameter values
   def readParValue(self, file, sheet):
      """ Read parameter short names and values from an Excel-file from defined sheet. For use in the notebook!
          Return a dictionary."""
      
      parValue = self.parValue
      
      parValue_local = {} 
      table = pd.ExcelFile(file).parse(sheet)
      for k in list(range(len(table))):
         parValue_local[table['Par'][k]] = table['Value'][k]
      parValue.update(parValue_local)

   # Define how to read dictionary for parameter location
   def readParLocation(self, file, sheets):
      """ Read parameter short and long names from an Excel-file sheet by sheet. For use in the notebook!
          Return a dictionary."""
      
      parLocation = self.parLocation      
      
      parLocation_local = {}
      for sheet in sheets:
         table = pd.ExcelFile(file).parse(sheet)
         for k in list(range(len(table))):
            parLocation_local[table['Par'][k]] = table['Location'][k]
      parLocation.update(parLocation_local)
 
   # Define function par() for parameter update
   def par(self, *x, **x_kwarg):
      """ Set parameter values if available in the predefined dictionary parValue. """
      
      parValue = self.parValue
      parCheck = self.parCheck      
      
      x_kwarg.update(*x)
      x_temp = {}
      for key in x_kwarg.keys():
         if key in parValue.keys():
            x_temp.update({key: x_kwarg[key]})
         else:
            print('Error:', key, '- seems not an accessible parameter - check the spelling')
      parValue.update(x_temp)
   
      parErrors = [requirement for requirement in parCheck if not(eval(requirement))]
      if not parErrors == []:
         print('Error - the following requirements do not hold:')
         for index, item in enumerate(parErrors): print(item)

   # Define function init() for initial values update
   def init(self, *x, **x_kwarg):
      """ Set initial values and the name should contain string '_start' to be accepted.
          The function can handle general parameter string location names if entered as a dictionary. """

      parValue = self.parValue      

      x_kwarg.update(*x)
      x_init={}
      for key in x_kwarg.keys():
         if '_start' in key: 
            x_init.update({key: x_kwarg[key]})
         else:
            print('Error:', key, '- seems not an initial value, use par() instead - check the spelling')
      parValue.update(x_init) 
   
   # Define fuctions similar to pyfmi model.get(), model.get_variable_descirption(), model.get_variable_unit()
   def model_get(self, parLoc):
      """ Function corresponds to pyfmi model.get() but returns just a value and not a list"""
      
      model_description = read_model_description(self.fmu_model)
#      model_description = self.model_description
      sim_res = self.sim_res
      start_values = self.start_values
      
      par_var = model_description.modelVariables
      for k in range(len(par_var)):
         if par_var[k].name == parLoc:
            try:
               if (par_var[k].causality in ['local']) & (par_var[k].variability in ['constant']):
                  value = float(par_var[k].start)                 
               elif par_var[k].causality in ['parameter']: 
                  value = float(par_var[k].start)  
               elif par_var[k].causality in ['calculatedParameter']: 
                  value = float(sim_res[par_var[k].name][0]) 
               elif par_var[k].name in start_values.keys():
                  value = start_values[par_var[k].name]   
               elif par_var[k].variability == 'continuous':
                  try:
                     timeSeries = sim_res[par_var[k].name]
                     value = float(timeSeries[-1])
                  except (AttributeError, ValueError):
                     value = None
                     print('Variable not logged')
               else:
                  value = None
            except NameError:
               print('Error: Information available after first simulation')
               value = None          
      return value
 
   # Define functions that mimic pyfmi-interacdtions 
   def model_get_variable_description(self, parLoc):
      """ Function corresponds to pyfmi model.get_variable_description() but returns just a value and not a list"""
      
      model_description = read_model_description(self.fmu_model)   
      
      par_var = model_description.modelVariables
      value = [x.description for x in par_var if parLoc in x.name]   
      return value[0]
   
   def model_get_variable_unit(self, parLoc):
      """ Function corresponds to pyfmi model.get_variable_unit() but returns just a value and not a list"""
      
      model_description = read_model_description(self.fmu_model)   
      
      par_var = model_description.modelVariables
      value = [x.unit for x in par_var if parLoc in x.name]
      return value[0]
                               
   # Define function disp() for display of initial values and parameters
   def disp(self, name='', decimals=3, mode='short'):
      """ Display intial values and parameters in the model that include "name" and is in parLocation list.
          Note, it does not take the value from the dictionary parValue but from the model. """
      
      parValue = self.parValue 
      parLocation = self.parLocation 
   
      def dict_reverser(d):
         seen = set()
         return {v: k for k, v in d.items() if v not in seen or seen.add(v)}
   
      if mode in ['short']:
         k = 0
         for Location in [parLocation[k] for k in parValue.keys()]:
            if name in Location:
               if type(self.model_get(Location)) != np.bool_:
                  print(dict_reverser(parLocation)[Location] , ':', np.round(self.model_get(Location),decimals))
               else:
                  print(dict_reverser(parLocation)[Location] , ':', self.model_get(Location))               
            else:
               k = k+1
         if k == len(parLocation):
            for parName in parValue.keys():
               if name in parName:
                  if type(self.model_get(Location)) != np.bool_:
                     print(parName,':', np.round(self.model_get(parLocation[parName]),decimals))
                  else: 
                     print(parName,':', self.model_get(parLocation[parName])[0])

      if mode in ['long','location']:
         k = 0
         for Location in [parLocation[k] for k in parValue.keys()]:
            if name in Location:
               if type(self.model_get(Location)) != np.bool_:       
                  print(Location,':', dict_reverser(parLocation)[Location] , ':', np.round(self.model_get(Location),decimals))
            else:
               k = k+1
         if k == len(parLocation):
            for parName in parValue.keys():
               if name in parName:
                  if type(self.model_get(Location)) != np.bool_:
                     print(parLocation[parName], ':', dict_reverser(parLocation)[Location], ':', parName,':', 
                        np.round(self.model_get(parLocation[parName]),decimals))

#------------------------------------------------------------------------------------------------------------------

   # Set the pen for the diagrams
   def setPen(self, lines_new):
      self.lines = lines_new

   # Reset the pen for the diagrams
   def resetPen(self):
      self.linecycler = cycle(self.lines)

   # Show plots from sim_res, just that
   def show(self):
      """Show diagrams chosen by newplot()"""
            
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
      for command in diagrams: eval(command, {}, context) 
 
#------------------------------------------------------------------------------------------------------------------    
      
   # Simulation
   def simu(self, simulationTime=None, mode='Initial', options=None):        
      """Model loaded and given intial values and parameter before,
         and plot window also setup before."""
      
      if simulationTime is None:
         simulationTime = self.simulationTime
         
      if options is None:
         options=self.options
  
      diagrams = self.diagrams 
      ax = self.ax  
      linecycler = self.linecycler
      timeDiscreteStates = self.timeDiscreteStates      
      stateValue = self.stateValue
      stateValueInitial = self.stateValueInitial
      stateValueInitialLoc = self.stateValueInitialLoc
      keyVariables = self.keyVariables      
      parValue = self.parValue
      parLocation = self.parLocation
      fmu_model = self.fmu_model
      model_description = read_model_description(fmu_model)  
      external_function = self.external_function  
      
      # Global variables
      global prevFinalTime
   
      # Simulation flag
      simulationDone = False
           
      # Internal help function to extract variables to be stored
      def extract_variables(diagrams):
          output = []
          variables = [v for v in model_description.modelVariables if v.causality == 'local']
          for j in range(len(diagrams)):
              for k in range(len(variables)):
                  if variables[k].name in diagrams[j]:
                      output.append(variables[k].name)
          return output

      # Run simulation
      if mode in ['Initial', 'initial', 'init']: 
      
         start_values = {parLocation[k]:parValue[k] for k in parValue.keys()}         
         stateValueInitial = self.stateValueInitial
         stateValueInitialLoc = self.stateValueInitialLoc
      
         # Simulate
         sim_res = simulate_fmu(
            filename = fmu_model,
            validate = False,
            start_time = 0,
            stop_time = simulationTime,
            output_interval = simulationTime/options['NCP'],
            record_events = True,
            start_values = start_values,
            fmi_call_logger = None,
            output = list(set(extract_variables(diagrams) + list(stateValue.keys()) + keyVariables))
         )
         self.start_values = start_values
         self.sim_res = sim_res
         self.t = sim_res['time']      
         simulationDone = True
      
      elif mode in ['Continued', 'continued', 'cont']:
      
         if prevFinalTime == 0: 
            print("Error: Simulation is first done with default mode = init'")
         
         else:         
            # Update parValueMod and create parLocationMod
            parValueRed = parValue.copy()
            parLocationRed = parLocation.copy()
            for key in parValue.keys():
               if parLocation[key] in stateValueInitial.values(): 
                  del parValueRed[key]  
                  del parLocationRed[key]
            parLocationMod = dict(list(parLocationRed.items()) + list(stateValueInitialLoc.items()))
   
            # Create parValueMod and parLocationMod
            parValueMod = dict(list(parValueRed.items()) + 
               [(stateValueInitial[key], stateValue[key]) for key in stateValue.keys()])      

            start_values = {parLocationMod[k]:parValueMod[k] for k in parValueMod.keys()}
  
            # Simulate
            sim_res = simulate_fmu(
               filename = fmu_model,
               validate = False,
               start_time = prevFinalTime,
               stop_time = prevFinalTime + simulationTime,
               output_interval = simulationTime/options['NCP'],
               record_events = True,
               start_values = start_values,
               fmi_call_logger = None,
               output = list(set(extract_variables(diagrams) + list(stateValue.keys()) + keyVariables))
            )
            self.start_values = start_values
            self.sim_res = sim_res
            self.t = sim_res['time']   
            simulationDone = True
      else:
      
         print("Error: Simulation mode not correct")

      if simulationDone:
         
         # Extract data
         t = self.t
      
         # Plot diagrams from simulation
         linetype = next(linecycler)
         context = locals().copy()
         context[self.external_function.__name__] = self.external_function
#         context[self.model_get.__name__] = self.model_get                       # <------ ver 1.1.6 perhaps
             
         for command in diagrams: eval(command, {}, context) 
   
         # Store final state values in stateValue:        
         for key in list(stateValue.keys()): stateValue[key] = self.model_get(key)  
         
         # Store time from where simulation will start next time
         prevFinalTime = sim_res['time'][-1]
      
      else:
         print('Error: No simulation done')    

#------------------------------------------------------------------------------------------------------------------

   # Describe model parts of the combined system
   def describe_parts(self, component_list=[]):
      """List all parts of the model""" 
      
      model_description = self.model_description
      
      def model_component(variable_name):
         i = 0
         name = ''
         finished = False
         if not variable_name[0] == '_':
            while not finished:
               name = name + variable_name[i]
               if i == len(variable_name)-1:
                   finished = True 
               elif variable_name[i+1] in ['.', '(']: 
                   finished = True
               else: 
                   i=i+1
         if name in ['der', 'temp_1', 'temp_2', 'temp_3', 'temp_4', 'temp_5', 'temp_6', 'temp_7']: name = ''
         return name
    
      variables = [v.name for v in model_description.modelVariables]
        
      for i in range(len(variables)):
         component = model_component(variables[i])
         if (component not in component_list) \
         & (component not in ['','BPL', 'Customer', 'today[1]', 'today[2]', 'today[3]', 'temp_2', 'temp_3']):
            component_list.append(component)
      
      print(sorted(component_list, key=str.casefold))
   
   def describe_MSL(self):
      """List MSL version and components used"""
      
      MSL_usage = self.MSL_usage
      
      print('MSL:', MSL_usage)

   # Describe parameters and variables in the Modelica code
   def describe_general(self, name, decimals):
      
      parLocation = self.parLocation
      fmu_model = self.fmu_model
  
      if name == 'time':
         description = 'Time'
         unit = 'h'
         print(description,'[',unit,']')
      
      elif name == 'process':
         print(read_model_description(fmu_model).description)   
      
      elif name in parLocation.keys():
         description = self.model_get_variable_description(parLocation[name])                
         value = self.model_get(parLocation[name])
         try:
            unit = self.model_get_variable_unit(parLocation[name])
         except FMUException:
            unit =''
         if unit =='':
            if type(value) != np.bool_:
               print(description, ':', np.round(value, decimals))
            else:
               print(description, ':', value)            
         if value is not None:
           print(description, ':', np.round(value, decimals), '[',unit,']')
                         
      else:
         description = self.model_get_variable_description(name)
         value = self.model_get(name)
         try:
            unit = self.model_get_variable_unit(name)
         except FMUException:
            unit =''
         if unit =='':
            if type(value) != np.bool_:
               print(description, ':', np.round(value, decimals))
            else:
               print(description, ':', value)     
         else:
            print(description, ':', np.round(value, decimals), '[',unit,']')


   # Plot process diagram
   def process_diagram(self):  
      
      fmu_model = self.fmu_model
      fmu_process_diagram = self.fmu_process_diagram
      
      try:
          process_diagram = zipfile.ZipFile(fmu_model, 'r').open('documentation/processDiagram.png')
      except KeyError:
          print('No processDiagram.png file in the FMU, but try the file on disk.')
          process_diagram = fmu_process_diagram
      try:
          plt.imshow(img.imread(process_diagram))
          plt.axis('off')
          plt.show()
      except FileNotFoundError:
          print('And no such file on disk either')

   # Describe FMU_explore commands
   def FMU_explore_info(self):
      print()
      print('Model for the process has been setup. Key commands:')
      print(' - par()       - change of parameters and initial values')
      print(' - init()      - change initial values only')
      print(' - simu()      - simulate and plot')
      print(' - newplot()   - make a new plot')
      print(' - show()      - show plot from previous simulation')
      print(' - disp()      - display parameters and initial values from the last simulation')
      print(' - describe()  - describe culture, broth, parameters, variables with values/units')
      print()
      print('Note that both disp() and describe() takes values from the last simulation')
      print('and the command process_diagram() brings up the main configuration')
      print()
      print('Brief information about a command by help(), eg help(simu)') 
      print('Key system information is listed with the command system_info()')

   # Dexribe framework 
   def system_info(self):
      """Print system information"""
      
      MSL_version = self.MSL_version
      BPL_version = self.BPL_version       
      FMU_explore_version = self.FMU_explore_version
      fmu_model = self.fmu_model
      model_description = self.model_description          
      
      constants = [v for v in model_description.modelVariables if v.causality == 'local']
   
      print()
      print('System information')
      print(' -OS:', platform.system())
      print(' -Python:', platform.python_version())
      try:
         scipy_ver = scipy.__version__
         print(' -Scipy:',scipy_ver)
      except NameError:
         print(' -Scipy: not installed in the notebook')
      print(' -FMPy:', version('fmpy'))
      print(' -FMU by:', read_model_description(fmu_model).generationTool)
      print(' -FMI:', read_model_description(fmu_model).fmiVersion)
      if model_description.modelExchange is None:
          print(' -Type: CS')
      else:
          print(' -Type: ME')
      print(' -Name:', read_model_description(fmu_model).modelName)
      print(' -Generated:', read_model_description(fmu_model).generationDateAndTime)
      print(' -MSL:', MSL_version)    
      print(' -Description:', BPL_version)   
      print(' -Interaction:', FMU_explore_version)
            
   # Acknowledgement
   def SDG(self, explanation=False):
     if explanation:
       print('"Soli Deo Gloria"')
       print(' It is latin and means "To the honour of God".') 
       print(' The great composer Johan Sebastian Bach used to end his compositions with this small remark SDG.')
       print(' And I like to do that too :).')    