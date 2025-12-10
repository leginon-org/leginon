-   [When Leginon or Leginon Client is launched,Python window opens and closes instantaneously on Windows](/leginon/Leginon_Manual/Installation_Troubleshooting/Test_run_operation_problems#Python-and-Leginon-windows-do-not-stay-opened-on-Windows-PC)


-   [ImportError "No module named xxxx"](/leginon/Leginon_Manual/Installation_Troubleshooting/Test_run_operation_problems#Missing-modules)


-   [Microscope or CCDCamera name does not show up in the
    Leginon instrument list in Instrument Node](/leginon/Leginon_Manual/Installation_Troubleshooting/Test_run_operation_problems#Tecnai-does-not-show-up-in-instrument-list)


-   [The Microscope computer where Leginon Client runs does
    not show up in the Launcher list of Leginon when opening an application](/leginon/Leginon_Manual/Installation_Troubleshooting/Test_run_operation_problems#Tecnai-does-not-show-up-in-instrument-list)


-   [No Magnification saved for xxx(your
    scope)](/leginon/Leginon_Manual/Installation_Troubleshooting/Test_run_operation_problems#Magnification-list-not-in-the-database)


-   [Leginon fails to collect 4kx4k images](/leginon/Leginon_Manual/Installation_Troubleshooting/Test_run_operation_problems#Leginon-fails-to-aquire-and-save-larger-images)

## Python and Leginon windows do not stay opened on Windows PC

***Why:***

-   Windows closes the python process window because an error is detected.

*_Testing: Start Leginon from a python command window so that the error message can be
read_*

-   Follow the following menu to open a python command window:

Windows/Start Menu/All Programs/Python2.5/Python (command line)

-   Python> import start


-   Read the error message. Copy it to your bug report when asking NRAMM for
    help.

## Missing modules

***Why:***

-   Either the python path is not set up correctly or the module was not installed
    properly.

***Testing:***

-   script: syscheck.py

If the missing module is not installed under one of the Python module search path
found in the syscheck output, it need to be moved.

## "Tecnai" does not show up in instrument list

***Why:***

-   An error is detected when the instrument is loaded.

*_Testing: Import the module in pyScope package through a python command window so that
the error message can be read*_

-   Follow the following menu to open a python command window:

Windows/Start Menu/All Programs/Python2.5/Python (command line)

-   *
    Follow instruction in updated from pyScope Bulletin Board Thread [Testing if pyScope is working with your TEM or CCD](http://emg.nysbc.org/redmine/boards/7/topics/607).

For example, if "Tecnai" is missing from the instrument list, try

    Python>from pyscope import registry
    Python>registry.getClasses()
    Python> myscope = registry.getClass('Tecnai')()
    Python> myscope.getMagnification()

-   The "registry.getClasses() command will show you in tuples, the class name, followed by the class object. Use the class name as the input for getClass command.


-   Read the error message. Copy it to your bug report when asking for help.

## Magnification list not in the database

***Why:***
first time the TEM is used by leginon and the database, the valid magnification
for the instrument needs to be saved in the database.

Solution: On the scope: Leginon/Instrument> select the microscope to display
parameters and click "Get Magnification" button (The icon is of a calculator) on the
tool bar.

## Leginon fails to aquire and save larger images

***Why:***

-   Your computer does not have sufficient memory to acquire and correct the large 4kx4k
    images.

Solution:

Put on your computer more memory and more memory swap space.

-   If you file storage system is not on the same computer, there may be problem
    transfering large data file. This is known to happen from a Windows machine to disk
    storage operated under Linux through Samba.

Solution:

Let us know if you have one.

## Leginon fails to move the goniometer after a new installation or update of pyScope

***Why:***

-   tecnaicom.py, the python wrapper of Tecnai Scripting library, has not been created
    in the running pyScope folder on the microscope controlling computer.

Solution:

Double click updatecom.py to run it in the (installed) pyScope folder.

[< Administration Tool problems](/leginon/Leginon_Manual/Installation_Troubleshooting/Administration_Tool_problems) | [Network problems >](/leginon/Leginon_Manual/Installation_Troubleshooting/Network_problems)
