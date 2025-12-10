# Falcon/Orius combo unique installation and setup

## Falcon/Orius is controlled by the same computer as the microscope

Currently working configuration uses TIA and TIA Scripting to control Falcon and Gatan Digital Micrograph Scripting to control Orius.

## Extra Package and Installation

-   Use all 32-bit version of Windows installer
    |*.program/package|*.notes|
    |TecnaiCCD.dll | For Orius to be controlled through DM. Should come with the microscope |
    |Tia.dll | For Falcon to be controlled through ESVision(TIA). Should come with the microscope |



------------------------------------------------------------------------

Program package web site local copy of win32 installer
comtypes 0.6.2 [http://sourceforge.net/projects/comtypes](http://sourceforge.net/projects/comtypes/files/comtypes/0.6.2/comtypes-0.6.2.win32.exe") comtypes-0.6.2.win32.exe
------------------------ ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -------------------------------------------------------------------------------------------------------------------------------------


### Register TecnaiCCD.dll for Orius (It may have been registered already)

-   From the command prompt, run the following commands. You may need to enter the full path of the dll:
        REGSVR32 TecnaiCCD.dll


## Comtypes installation

## THIS INSTRUCTION IS FOR comtypes 0.6.2. If you install newer version, this may not work.

### Double click on the installer

### Modify comtypes

IMPORTANT: After installing comtypes, you must make one modification to it. The module "safearray.py" that comes with comtypes must be replaced with a modified version that we provide. You can find the custom version of safearray.py in the pyscope package. Please copy this module from pyscope into the installed comtypes folder: C:\Python2*\Lib\site-packages\comtypes. It should replace the safearray.py that is included in comtypes.

Remove safearray.pyc in C:\Python2*\Lib\site-packages\comtypes\ if it does not appear to recompile (timestamp of the file change) when you import comtype in python command line

import comtypes

### Run checkcom.py

- From a command line window:
cd C:\python27\Lib\site-packages\pyscope
C:\python27\python.exe checkcom.py

The module it finds depends on the module.


For DM scripting

    Found COM typelib named:  TecnaiCCD.

and one of these outputs for TIA scripting

    Found COM typelib named: ESVision.Application done.

## instruments.cfg


[Falcon Camera]
class:tia.TIA_Falcon
zplane: 50
width: 4096
height: 4096

[Orius]
class:gatan.Gatan
zplane:49
width: 2048
height: 2048

- Note that the class name for Gatan DM controlled camera depends on the number of cameras. Ask us if you have more than one and need to find out which is which.


## Setup

-   Set camera configuration to give the [standard Leginon orientation](/leginon/Leginon_Manual/Instrument_Set-up/Leginon_image_orientation). For example, we need 270 degree rotation and flip around the vertical axis on FEI F20. Note that the rotation required is different if it is installed post-GIF and/or on Krios.
-   Set the [shutter configuration in DM](/leginon/Leginon_Manual/Instrument_Set-up/Low_dose_shutter_configuration_for_Gatan_camera_in_Digital_Micrograph_program) to protect the specimen when camera is not taking images.
-   Create the folder to store the dose fractionation raw frames. Frames are saved as unsigned 16-bit mrc image stack in K2 computer under D:\frames by default as set in the code inside pyscope/dmsem.py in the function calculateFileSavingParams. You must create the frames directory first. Leginon will not do that for you. You may change where the frames are saved here but will need to make corresponding changes when setting up [raw frame file transfer](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Direct_Electron_DE-12_direct_detection_device_support/DDD_raw_frame_file_transfer)
-   Setup [raw frame file transfer](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Direct_Electron_DE-12_direct_detection_device_support/DDD_raw_frame_file_transfer) from a network data server.
-   Unless you want to develop your own frame alignment program. We recommend that you [use Appion to do frame gain correction and alignment](/leginon/appionDirect_Detector_Frame_Processing). These are parallelized by images so it cam almost keep up with the acquisition.

## Testing with pyscope

Type these commands in python IDLE if you want to see the error message.

### Testing Orius

    from pyscope import gatan
    g = gatan.Gatan()
    g.setExposureTime(100)
    g.getImage()

### Testing Falcon

    from pyscope import tia
    g = tia.TIA_Falcon()
    g.setExposureTime(1000)
    g.getImage()


You should expect these to run without error. The getImage() command should give a 2D numpy array like

array([[1000, 3400, 2300, ..., 1000,1200,3000],
[1000, 3400, 2300, ..., 1000,1200,3000],
[1000, 3400, 2300, ..., 1000,1200,3000],
...,
[1000, 3400, 2300, ..., 1000,1200,3000],
[1000, 3400, 2300, ..., 1000,1200,3000],
[1000, 3400, 2300, ..., 1000,1200,3000],dtype=int16)

The number and dtype depends on the camera.

a.shape command should give a tuple of the camera dimension matching your camera.
For example, (4096,4096)

**If you use python shell to do this test, some of the error will cause the shell window to close immediately. Use Python IDLE instead in that case**


## Programs to open before Leginon Client: Digital Micrograph and then TIA
