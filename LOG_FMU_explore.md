# LOGBOOK OF FMU\_explore DEVELOPMENT
 
Here I describe the status of development the module FMU\_explore. The code has been developed over long time as a gernal part of a setup script for BPL applications. Now the time has come to encapsulate this code as a central module. The simplified FMU interaction can be used for Modelica simulation models in general and not just BPL applications. 

This informal text briefly describes the status and goals in near time. The idea is that this text here will complement the formal git-version handling. Now and then I plan to introduce reference to the git-version commit history. 
 
Key architecture features are:

* Class structure of the module
* The module is then adapted to an applications through a number of variables
* The module placed in a package to simplify future use both locally and in Github

Development is mainly done in the following files:

* fmu\_explore\_pyfmi.py
* fmu\_explore\_fmpy.py
* setup TEST2\_Batch.py
* setup TEST2\_Batch\_explore.py



I think the different examples serve as a good test bench for changes in the library. The collection of processes also is a good starting point when new systems are developed.

A general goal is: 
 
Specific goals - now reached: 

* Module v1  without simu(), show(), setLines() / Done 260819
* Module v2 complete a new concept axes as a list / Done 260819
* Module v2 now works in Windows with PyFMI / Done 260820
* Module v2 now works in Linux with PyFMI and no surprises / Done 260821
* Module v2 stored in package and used both locally and in Colab  / Done 260824
* How do I make the performance function cstrProdMax() available inside simu() / Done 260825
* Make sim_res available in the Jupyter/Colab notebook when needed / Done 260829
* Make declaration of version in only one place from todays three places
* Make simulationTime default for simu() and also possible to set in simu() / Done 260901
* Make options in simu() possible to set / Done 260901
* **Make version of scipy.optimize visible in system_info()**
* Make cstrProdMax() available during plotting
* Make profile() available during plotting


## Day to day notes in reversed time order 
Note that commit ID are now given after the date and description (i.e. opposite to Git).  Far from all commits are described here though. 

2026-09-01 Brought in BPL\_TEST2\_Batch\_calibration.

2026-09-01 I made simu() have parameters simultionTime and options free to set but default taken from the class. Call it **FMU\_explorer ver 1.1.3**.

2026-08-28 Now brought in BPL\_YEAST\_COB\_Batch and BPL\_TEST2\_Batch\_design_space using FMU\_explore ver 1.1.2

2026-08-29 I made sim_res available outside simu() by just introducting a return statement in the function. Call this **FMU\_explorer ver 1.1.2**.

2026-08-28 Now brought in BPL\_IEC\_Operation, BPL\_STEM\_AIR\_Perfusion.

2026-08-27 Now brought in BPL\_CHO\_Perfusion_cspr_openloop.

2026-08-26 Now brought three more applications to Colab: PL\_TEST2\_Chemostat, BPL\_YEAST_AIR\_Fedbatch, BPL\_CHO\_Fedbatch.   

2026-08-25 Almost managed to convert BPL\_TEST2\_Chemostat for FMU\_explore 1.1.0. Remains to handle cstrProdMax() defined in user functions, though. 

2026-08-24 The package updated to include import of pandas. Then run locally with BPL\_TEST2\_Batch, BPL\_TEST2\_Fedbatch and BPL\_CHO\_Fedbatch in Windows. The next step is to run these applications also in Colab after updating the Colab notebook. Problem today with pyfmi more general.

2026-08-21 I tested the application BPL\_TEST2\_Batch in Linux and worked fine. Then I made it public at Github Colab and published a note as well.

2026-08-20 I decided to let the itertool work from the module only. The function resetPen() can be used in the function newplot() in the applications script and that is the key. Also the sim\_res file is for the time being just kept global from the module.

2026-08-19 Managed to get v2 working reasonbly. The key was to introduce an empty list ax, similar to diagrams, as part of the class. Then newplot() gives both of them appropirate values. Remains to fix setLines() and also simu() bring back start and final simulation time.
