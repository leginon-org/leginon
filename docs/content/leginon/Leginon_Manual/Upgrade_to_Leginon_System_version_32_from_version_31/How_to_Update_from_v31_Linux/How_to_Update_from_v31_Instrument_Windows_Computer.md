The changes to v3.2 DOES require upgrade at the microscope and camera computers.

See [Installation Troubleshooting](/leginon/Leginon_Manual/Installation_Troubleshooting) and [Leginon Bulletin Board](http://emg.nysbc.org/redmine/projects/leginon/boards) searching
for "install" if you run into problems.

## Download myami-3.2 source code

### Check out SVN Source Files from the repository

Assuming that you have installed some kind of svn client such as TortoiseSVN "http://tortoisesvn.tigris.org/", you can use your mouse to do the following

-   Create myami3.2 directory somewhere at your convenience
-   Change directory into myami3.2
-   Right-click the mouse botton in this directory window and select Tortoise svn
    Checkout in the menu: ![](images/svnmenu.png)
-   Set up svn checkout window like this, but check out from http://emg.nysbc.org/svn/myami/branches/myami-3.2 and save it to myami3.2 folder ![](images/svnco.png)

Otherwise, you can copy the files from your linux myami-3.2 source.

## Move your existing packages to a backup directory (Optional):

At the beginning of the syscheck.py output, the location of the exisiting Leginon folder is shown. Although new installation overwrite the old in most cases, problem has been observed in the past. Therefore, it is best to remove the old files from the path before new installation. Better yet, copy into a backup folder because we need some configuration files from them.
You may find these folders here:
|leginon|
|pyscope|
|sinedon|
|pyami|

For example, your installed Leginon folder is at C:\python27\Lib\site-packages\leginon

    Go to C\python27\site-packages
    Create Leginon3_1_backup folder
    Move Leginon folder into Leginon3_1_backup folder

## Install subpackages you downloaded from NRAMM svn repository. **You should not install numextension, libcv and comarray using this instruction**

-   Start a command line Window from Start Menu


-   Reinstall the package in EACH of the following folders using the included setup.py
    |leginon|
    |pyscope|
    |sinedon|
    |pyami|


    cd Your_Download_Place\myami3.2_folder
    c:\python27\python.exe setup.py install


## Locate global configuration directory following standard on Windows

Saving cfg files in a global location reduces future need for copying old configuration to updated installation. The location is different for different versions of Windows. To locate the one for your Windows version:

1. go to C:\python27\Lib\site-packages\leginon
2. run configcheck.py

The script gives the three search directories of the cfg files and the loaded file if present. Note the first search directory that with a name most likely start with **C:\Programs** and ends with **\myami**. This is the **global configuration directory** we will use.


## copy the old config files to the global location if you still use local files

## Install comtypes on FEI scope controlling computer

We have switched to use comtypes exclusively in 3.2.

See [32-bit](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_microscope_computer_30/FEI_TecnaiTitan_installation_specifics) or [64-bit](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_microscope_computer_30/FEI_Talos_installation_specifics) computer instruction depending on your system although know that to communicate with the instrument, the 32-bit python and subpackages are always installed.

## Enter Tietz PXL camera imaging size in instruments.cfg if needed in this format:

    [camera]
    tietz.TietzPXL
    zplane:10
    height: 2048
    width: 2048

## About [TEM Scripting Beam Tilt Calibration](/leginon/Leginon_Manual/Instrument_Set-up/Calibrations_required_on_FEI_microscopes/TEM_Scripting_Beam_Tilt_Calibration)

-   If you have done [TEM Scripting Beam Tilt Calibration](/leginon/Leginon_Manual/Instrument_Set-up/Calibrations_required_on_FEI_microscopes/TEM_Scripting_Beam_Tilt_Calibration) and have changed the scale factor in tecnai.py, you should copy the value to your new installation.

## Gatan K2 Summit camera

We moved the configuration from dmsem.py to a configuration file parsed with standard parser.

1.  Check your 3.1 pyscope/dmsem.py for the old configuration needed for the camera to indicate its DM version, orientation, and file saving location.
2.  Copy Your_Download_Place\myami3.2\pyscope\dmsem.cfg.template to the standard myami config path C:\Program File\myami\dmsem.cfg
3.  Modify dmsem.cfg according to your old configuration
    More details in [Gatan K2 installation and setup#(Version-3.2)-Define-local-configuration-in-dmsemcfg](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Gatan_K2_Summit_Support/Gatan_K2_installation_and_setup#(Version-3.2)-Define-local-configuration-in-dmsemcfg)


    ### general dm configurations
    [dm]
    # DM Version
    DM_VERSION = 2.31.734.0

    ### K2 Summit configuration through SERIALEMCCD plugin
    [k2]
    # Camera ID
    CAMERA_ID = 0
    # the value in DM camera config
    FLIP = True
    # multiple of 90 degrees (i.e. put 1 if 90 degrees, 3 if 270 degrees)
    ROTATE = 1
    # raw frame base directory. Use '\' as path separator
    RAW_FRAME_DIR = D:\frames
    # max number of frames to sum in order to return early
    EARLY_RETURN_FRAME_COUNT = 0

## Gatan K2 Summit camera changes upon GMS upgrade

A change in GMS 2.3.1 and SerialEMCCD which we use at the backend causes the frame saved at different orientation from the reference images saved in standard Leginon orientation. An up-down flip is required in general.

You must change dmsem.py to reflect this:

GMS upgrade to 3.0 is now tested in the field, and confirmed that functions are not affected.

[< How to Update from v3.0 (Linux)](/leginon/Leginon_Manual/Upgrade_to_Leginon_System_version_31_from_version_30/How_to_Update_from_v30_Linux)
