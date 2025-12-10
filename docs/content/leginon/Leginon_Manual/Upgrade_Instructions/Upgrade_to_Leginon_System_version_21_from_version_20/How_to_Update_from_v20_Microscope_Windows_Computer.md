The changes from v2.0 does not require upgrade at the microscope but is recommended.

See [Installation Troubleshooting](/leginon/Leginon_Manual/Installation_Troubleshooting) and [Leginon Bulletin Board](http://emg.nysbc.org/redmine/projects/leginon/boards) searching
for "install" if you run into problems.

## Packages required from NRAMM

All Leginon (and Appion) packages distributed from NRAMM are under one svn control.

Recommended minimal subpackage upgrade:
|pyscope|setting of beam tilt value scale factor|

## Download myami-2.1 source code

### Check out SVN Source Files from the repository

Assuming that you have installed some kind of svn client such as TortoiseSVN "http://tortoisesvn.tigris.org/", you can use your mouse to do the following

-   Create myami2.1 directory somewhere at your convenience
-   Change directory into myami2.1
-   Right-click the mouse botton in this directory window and select Tortoise svn
    Checkout in the menu: ![](images/svnmenu.png)
-   Set up svn checkout window like this, but check out from http://emg.nysbc.org/svn/myami/branches/myami-2.1 and save it to myami2.1 folder ![](images/svnco.png)

Otherwise, you can copy the files from your linux myami-2.1 source.

## Perform system check if you can't remember where you have installed your Leginon before.

-   Go to ~/myami2.1/leginon
-   Double click on syscheck.py

You should have all the supporting packages installed for v2.0. If you see any lines like "* Failed...", then you have something missing. Otherwise, everything should result in "OK".

## Move your existing packages to a backup directory (Optional):

At the beginning of the syscheck.py output, the location of the exisiting Leginon folder is shown. Although new installation overwrite the old in most cases, problem has been observed in the past. Therefore, it is best to remove the old files from the path before new installation. Better yet, copy into a backup folder because we need some configuration files from them.
You may find these folders here:
|leginon|
|pyscope|
|sinedon|
|pyami|
|imageviewer|

For example, your Leginon folder is at C:\python25\Lib\site-packages\leginon

    Go to C\python25\site-packages
    Create Leginon2_0_backup folder
    Move Leginon folder into Leginon2_0_backup folder

## Install subpackages you downloaded from NRAMM svn repository. **You should not install numextension, libcv and comarray using this instruction**

-   Start a command line Window from Start Menu


-   Reinstall the package in EACH of the following folders using the included setup.py
    |leginon|
    |pyscope|
    |sinedon|
    |pyami|
    |imageviewer|


    cd Your_Download_Place\myami2.1_folder
    c:\python25\python.exe setup.py install

-   run syscheck.py again to make sure you have everything.

## Copy your Leginon2.0 sinedon.cfg to the new installation if you have moved the Leginon2.0 installation into its backup.

-   Find your sinedon.cfg. Depending on your previous setting, look in the directories listed here in order:
    *your home directory as described in syscheck.py
    *The sinedon directory where it is called from. If unsure, start python command line and type these to find out:
        python> import sinedon
        python> sinedon


-   If sinedon.cfg reside in the installed sinedon subpackage, you should copy it from your Leginon2.0 backup to the new installation.
        go to  C:\python25\Lib\site-packages
        copy Leginon_2_0_backup\sinedon\sinedon.cfg  into the new sinedon folder

## Copy your Leginon2.0 Instruments.cfg to the new installation if you have moved Leginon2.0 installation into its backup:

-   instruments.cfg is in the pyscope folder of your Leginon 2.0 backup to the new pyscope folder under site-packages directory.

## modify Tietz PXL camera imaging size if you did so before for Leginon 2.0

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

## Perform [TEM Scripting Beam Tilt Calibration](/leginon/Leginon_Manual/Instrument_Set-up/Calibrations_required_on_FEI_microscopes/TEM_Scripting_Beam_Tilt_Calibration) in case your TEM Scripting requires non-unity scale factor

[< How to Update from v2.0 (Linux)](/leginon/Leginon_Manual/Upgrade_Instructions/Upgrade_to_Leginon_System_version_21_from_version_20/How_to_Update_from_v20_Linux)
