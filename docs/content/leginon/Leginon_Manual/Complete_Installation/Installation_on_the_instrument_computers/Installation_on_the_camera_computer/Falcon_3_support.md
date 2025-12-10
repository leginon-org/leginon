## Requirement from camera manufacture:

-   Krios 2.12 or Talos/Arctica 1.12 software version.
-   Advanced TEM Scripting

## Required leginon version:

-   3.4 and above

## Extra Package and Installation

  program/package            notes
  -------------------------- -----------------------------------
  TEMAdvancedScripting.dll   (Should come with the microscope)



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


You should have

    TEMAdvancedScripting

## instruments.cfg

-   Falcon3 class is for linear mode and Falcon3EC class is for electron counting mode. You want to have both. The configuration section names just need to be unique. In this case, we call them camera1 and camera2, respectively.
        [camera1]
        class: feicam.Falcon3
        zplane: 50
        height: 4096
        width: 4096

        [camera2]
        class: feicam.Falcon3EC
        zplane: 50
        height: 4096
        width: 4096

## Setup

-   Set dose rate and acquire References using TUI Reference manager. Don't do it in Leginon.
-   Set up in fei.cfg (See FEI scope installation instruction)
        [camera]
        FRAME_SUBPATH = leginonframes

    
    In this case, you will need to create a directory called leginonframes on your Falcon image storage server (called OffloadData on your scope PC) with these parent directories
        OffloadData\TemScripting\BM-Falcon\leginonframes

This leginonframes directory can then mounted on your permanent storage system and allow rawtransfer.py to rsync the files.

## Programs to open before Leginon Client: TIA.

## Testing with pyscope

In python command

    form pyscope import feicam
    g = feicam.Falcon3()
    g.setExposureTime(200)
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


## Trouble shooting

If TEM Advanced Scripting is not setup correctly by the manufacture, a configuration error will appear similar to this:

    _ctypes.COMError: (-2147467259, 'Unspecified error.', (u"Could not load Storage Server configuration file: C:\ProgramData\FEI||AcquisitionStorageServer||StorageServer.config', u'',u'', 0, None))
