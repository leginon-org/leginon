The changes from v1.6 requires update of all in-house components of Leginon, dbemtools and database but not the php-mrctools.
Don't forget that you need to also update the packages on the microscope-controlling computer
since the pyScope update need to be synchronized.

See [Installation Troubleshooting](/leginon/Leginon_Manual/Installation_Troubleshooting) and [Leginon Bulletin Board](http://emg.nysbc.org/redmine/projects/leginon/boards) searching
for "install" if you run into problems.

## Packages required from NRAMM

All Leginon (and Appion) packages distributed from NRAMM are now under one svn control.

A few updates are needed for preparation of python 3.0 compatibility where the method for importing module is changed. They will still run under python 2.5 and up.
Here are the packages you need to install with python installer

  SVN subPackage Name   Reason for update:
  --------------------- -------------------------------------------
  leginon               new features
  pyami                 new features
  sinedon               required for updating database
  pyscope               new method for creating pythoncom modules
  imageviewer           debug

Because numextension and libcv requires extra compiler, we have created
window installer for them for python 2.5 and made them available at http://emg.nysbc.org/redmine/projects/leginon/files.

  Downloadfile Name                    Purpose:
  ------------------------------------ ---------------------------------------------------------
  numextension-2.0.0.win32-py2.5.exe   c extension for numerical processing
  comarray-2.0.0.win32-py2.5.exe       com module output conversion to array
  libCV-0.2.win32-py2.5.exe            small c library of algorithm from computer vision field

## Download Leginon 2.0 source code

### Check out SVN Source Files from the repository

Assuming that you have installed some kind of svn client such as TortoiseSVN "http://tortoisesvn.tigris.org/", you can use your mouse to do the following

-   Create Leginon2.0 directory somewhere at your convenience
-   Change directory into Leginon2.0
-   Right-click the mouse botton in this directory window and select Tortoise svn
    Checkout in the menu: ![](images/svnmenu.png)
-   Set up svn checkout window like this, but check out from http://emg.nysbc.org/svn/myami/branches/myami-2.0 and save it to Leginon2.0 folder ![](images/svnco.png)

## Perform system check if you can't remember where you have installed your Leginon before.

-   Go to ~/Leginon2.0/leginon
-   Double click on syscheck.py

You should have all the supporting packages installed for v1.6. If you see any lines like "* Failed...", then you have something missing. Otherwise, everything should result in "OK".

## Uninstall your existing NRAMM packages:

Although new installation overwrite the old in most cases, problem has been observed in the past. Therefore, it is best to remove the old files before new installation.

Use "Add or Remove Programs" application in "Control Panel" to do this. Leginon related
packages are shown with prefix "Python 2.5"

Remove only packages from NRAMM but not the suppporting packages. The NRAMM packages that you may find in "Add or Remove Programs" are
|pyScope|
|numextension|
|comarray|
|libCV|

If you didn't use Installer to install previously, the packages may not show up in the
Programs list. Simply remove or rename the folder containing the old packages in this case as described next.

## Move your existing packages to a backup directory:

At the beginning of the syscheck.py output, the location of the exisiting Leginon folder is shown. Although new installation overwrite the old in most cases, problem has been observed in the past. Therefore, it is best to remove the old files from the path before new installation. Better yet, copy into a backup folder because we need some configuration files from them.
You may find these folders here:
|Leginon|
|pyScope|
|sinedon|
|pyami|
|ImageViewer|

For example, your Leginon folder is at C:\python25\Lib\site-packages\Leginon

    Go to C\python25\site-packages
    Create Leginon1_6_backup folder
    Move Leginon folder into Leginon1_6_backup folder

Be aware that in some cases the installed package name is different (capitalized) from your svn package name and that numextension amd libCV are not in its own subdirectory in the python library but just the compiled .so files

## Install the Windows Installer Files from Leginon website http://emg.nysbc.org/redmine/projects/leginon/files

Execute the installer files and follow the instructions.

## Install other subpackages you downloaded from NRAMM svn repository. You don't need to repeat ones you've already installed using the installer files.

-   Start a command line Window from Start Menu


-   Reinstall the package in EACH of the following folders using the included setup.py
    |leginon|
    |pyscope|
    |sinedon|
    |pyami|
    |imageviewer|


    cd Your_Download_Place\Leginon 2.0\install_folder
    c:\python25\python.exe setup.py install

-   run syscheck.py again to make sure you have everything.

## Copy your Leginon1.6 sinedon.cfg to the new installation

-   Find your sinedon.cfg. Depending on your previous setting, look in the directories listed here in order:
    *your home directory as described in syscheck.py
    *The sinedon directory where it is called from. If unsure, start python command line and type these to find out:
        python> import sinedon
        python> sinedon


-   If sinedon.cfg reside in the installed sinedon subpackage, you should copy it from your Leginon1.6 backup to the new installation.
        go to  C:\python25\Lib\site-packages
        copy Leginon_1_6_backup\sinedon\sinedon.cfg  into the new sinedon folder

## Copy your Leginon1.6 Instruments.cfg to the new installation:

-   instruments.cfg is in the pyScope folder of your Leginon 1.6 backup to the new pyscope folder under site-packages directory.

## Run updatecom.py

From a command line window:

    cd C:\python25\Lib\Site-Packages\pyScope
    C:\python25\python.exe updatecom.py

The python window appears should say show the required type libraries it found:

    Generating .py files from type libraries...
    initializing TEM Scripting Error, cannot find typelib for "TEM Scripting"
    initializing Tecnai Scripting done.
    initializing TOM Moniker done.
    initializing Tecnai Low Dose Kit done.
    initializing Tecnai Exposure Adaptor done.

    initializing Tietz CCD Camera done.


The output depending on what is available on your microscope computer. You should have either "Tecnai Scripting" or the pairing of "TEM Scripting" and "TOM Moniker".

The script should generate a few files in C:\python25\Lib\win32com\gen_py with seemly scrambled names such as BC0A2B03-19FF-11D3-AE00-00A024CBA50Cx0x1x9.py

## modify Tietz PXL camera imaging size if you did so before for Leginon 1.6

**You should not copy the old one in this case since the file has been changed**

-   Go to C:\Python25\Lib\site-packages\pyscope


-   Edit tietz.py with a plain text editor


-   Find the lines:


     def getCameraSize(self):
    # {'type': dict, 'values': {'x': {'type': int}, 'y': {'type': int}}}}
    x = self._getParameterValue('cpTotalDimensionX')
    y = self._getParameterValue('cpTotalDimensionY')
    return {'x': x, 'y': y}

-   Change the last line to:


        return {'x': 2048, 'y': 2048}

## Perform [TEM Scripting Beam Tilt Calibration](/leginon/Leginon_Manual/Instrument_Set-up/Calibrations_required_on_FEI_microscopes/TEM_Scripting_Beam_Tilt_Calibration) if this is an FEI microscope.

[< How to Update from v1.6 (Linux)](/leginon/Leginon_Manual/Upgrade_Instructions/Upgrade_to_Leginon_System_version_2x_from_version_16/How_to_Update_from_v16_Linux) | [Preparation before Using v2.x Routinely >](/leginon/Leginon_Manual/Upgrade_Instructions/Upgrade_to_Leginon_System_version_2x_from_version_16/Preparation_before_Using_v2x_Routinely)
