## Installation

  program/package   notes
  ----------------- -----------------------------------
  Tia.dll           (Should come with the microscope)



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

    TIA or ESVision

## instruments.cfg

Eagle:

    [camera]
    class: tia.TIA_Eagle
    zplane: 50
    height: 4096
    width: 4096

## Testing with pyscope

In python command

    from pyscope import tia
    g = tia.TIA_Ceta()
    g.setExposureTime(1000)
    a=g.getImage()
    a.shape


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


## Using Ceta camera in Leginon

Leginon does not handle Gain/Dark correction for Ceta camera. It will not use Leginon-collected references even if you acquire them as it will make images worse.

Follow FEI's instruction in obtaining Gain/Dark References in the scope user interface.

Take an single exposure first in its Reference Manager Tab to make sure the intensity range is adequate.
