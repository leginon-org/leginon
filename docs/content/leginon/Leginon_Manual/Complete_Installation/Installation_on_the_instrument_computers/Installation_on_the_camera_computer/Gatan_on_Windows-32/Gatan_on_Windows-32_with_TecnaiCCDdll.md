-   TecnaiCCD.dll is provided by FEI to work with Gatan camera. This installation instruction is known to work when the camera control is on
    the same computer as the FEI scope control.


-   For JEOL microscope, or for camera separated from scope PC, [Gatan on Windows-32 with dmsem](/leginon/Gatan_on_Windows-32_with_dmsem) may be easier.

## Extra Package and Installation

  program/package   notes
  ----------------- -------
  TecnaiCCD.dll     



------------------------------------------------------------------------

Program package web site local copy of win32 installer
comtypes 0.6.2 [http://sourceforge.net/projects/comtypes](http://sourceforge.net/projects/comtypes/files/comtypes/0.6.2/comtypes-0.6.2.win32.exe") comtypes-0.6.2.win32.exe
------------------------ ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -------------------------------------------------------------------------------------------------------------------------------------


## Register TecnaiCCD.dll (Gatan 32-bit DM on FEI microscope), CAMC4.exe (For Tietz camera), and adaexp.exe (For film exposure)

-   From the command prompt, run the following commands. You may need to enter the full path of the exe or dll:
        adaexp.exe /regserver
        CAMC4.exe /regserver
        REGSVR32 TecnaiCCD.dll

In one case, we also had to [find and register TEM Scripting](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_microscope_computer_30/FEI_TecnaiTitan_installation_specifics/Unable_to_initializ_Tecnai_interface_error/Find_and_register_a_dll_file_as_command_components_in_Windows) for an FEI scope

## install comtypes if this is for the microscope, or any camera other than Gatan K2 Summit* nor TVIPS.



------------------------------------------------------------------------

Program package web site local copy of win32 installer
comtypes 0.6.2 [http://sourceforge.net/projects/comtypes](http://sourceforge.net/projects/comtypes/files/comtypes/0.6.2/comtypes-0.6.2.win32.exe") comtypes-0.6.2.win32.exe
------------------------ ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -------------------------------------------------------------------------------------------------------------------------------------



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


## Modify comtypes if it is used:

## instruments.cfg

    [camera]
    class: gatan.Gatan
    zplane: 50
    height: 4096
    width: 4096

-   height and width depend on your specific camera
    see [instruments.cfg z plane configuration](/leginon/Instrumentscfg_for_22) for more explanation.

If you have more than one camera controlled through DM, you need to find its id and use class gatan.Gatan0 and gatan.Gatan1 etc in the configuration to distinguish them and assign different zplanes so the higher ones can retract when the lower one is asked to acquire image. see #2201 for history of this issue

## Setup

-   Set camera configuration to give the [standard Leginon orientation](/leginon/Leginon_Manual/Instrument_Set-up/Leginon_image_orientation).
-   Set the [shutter configuration in DM](/leginon/Leginon_Manual/Instrument_Set-up/Low_dose_shutter_configuration_for_Gatan_camera_in_Digital_Micrograph_program) to protect the specimen when camera is not taking images

## Testing with pyscope

In python command

    from pyscope import gatan
    g = gatan.Gatan()
    g.setExposureTime(200)
    g.getImage()

You should get a bunch of numbers in a numpy array.

## Programs to open before Leginon Client: Digital Micrograph
