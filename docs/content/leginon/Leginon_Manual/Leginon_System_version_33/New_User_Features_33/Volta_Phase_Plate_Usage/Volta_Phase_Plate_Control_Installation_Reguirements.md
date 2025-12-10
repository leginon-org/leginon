## Install AutoIt and compile the script

The script you need is NextPhasePlate.au3


## Download AutoIt Scripting program on microscope computer

see https://www.autoitscript.com/site/autoit/downloads/

## Compile *.au3 files

These are found in your_myami/pyscope/autoit/. Right-click on the file icon should allow you to compile. Place the resulting exe files at a common place, for example, **C:\Program Files\AutoIt3** and remember its location to be added to fei.cfg


## configure fei.cfg

Add the full path to your compiled exe file to fei.cfg you use on the microscope computer.

    [phase plate]
    # Location of next phase plate AutoIt executable
    AUTOIT_PHASE_PLATE_EXE_PATH = C:\Program Files\AutoIt3\NextPhasePlate.exe

## testing NextPhasePlate.exe

1. Testing the script: double click NextPhasePlate.exe while the phase plate TUI displays the next phase plate button.
The script assumes specific location relative to its Aperture dialog window. If it is off, you will have to adjust the position in the au3 file.

You should see the cursor move to the button and the current patch number increment as a result of a successful run.

## testing from python script through pyscope/fei.py

    from pyscope import fei
    f = fei.Krios()
    f.getAutoitPhasePlateExePath()
    f.nextPhasePlate()

### Notes:

-   Use your instrument class in the second line if it is not Krios.
-   The third command should return the location of the NextPhasePlate.exe you entered in fei.cfg
-   The forth command should results in phase plate patch number increase by one.
