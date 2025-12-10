The changes to v3.0 DOES require upgrade at the microscope and camera computers.

We have compiled all pre-compiled installer with python 2.7 now. Therefore, you do best by following the [complete installation instruction](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers) until you reach the part for configuration.

See [Installation Troubleshooting](/leginon/Leginon_Manual/Installation_Troubleshooting) and [Leginon Bulletin Board](http://emg.nysbc.org/redmine/projects/leginon/boards) searching
for "install" if you run into problems.

## copy the old config files to the new location.

**If you want to avoid copying cfg files to new installation in the future, copy them from where you had it in the python2.5 2.2 installation to the global config directory**


## Locate global configuration directory following standard on Windows

Saving cfg files in a global location reduces future need for copying old configuration to updated installation. The location is different for different versions of Windows. To locate the one for your Windows version:

1. go to C:\python27\Lib\site-packages\leginon
2. run configcheck.py

The script gives the three search directories of the cfg files and the loaded file if present. Note the first search directory that with a name most likely start with **C:\Programs** and ends with **\myami**. This is the **global configuration directory** we will use.


  ----------------- -------------------------------------------------------------------
  *config file*     likely location in 2.2 installation if not in your home directory
  sinedon.cfg       C:\python25\Lib\site-packages\sinedon
  leginon.cfg       C:\python25\Lib\site-packages\leginon\config
  instruments.cfg   C:\python25\Lib\site-packages\pyscope
  ----------------- -------------------------------------------------------------------

## modify Tietz PXL camera imaging size if you did so before for Leginon 2.2

**You should not copy the old one in this case since the file has been changed**

-   Go to C:\Python27\Lib\site-packages\pyscope


-   Edit tietz.py with a plain text editor


-   Find the lines:


     def getCameraSize(self):
    # {'type': dict, 'values': {'x': {'type': int}, 'y': {'type': int}}}}
    x = self._getParameterValue('cpTotalDimensionX')
    y = self._getParameterValue('cpTotalDimensionY')
    return {'x': x, 'y': y}

-   Change the last line to:


        return {'x': 2048, 'y': 2048}

## About [TEM Scripting Beam Tilt Calibration](/leginon/Leginon_Manual/Instrument_Set-up/Calibrations_required_on_FEI_microscopes/TEM_Scripting_Beam_Tilt_Calibration)

-   If you have done [TEM Scripting Beam Tilt Calibration](/leginon/Leginon_Manual/Instrument_Set-up/Calibrations_required_on_FEI_microscopes/TEM_Scripting_Beam_Tilt_Calibration) and have changed the scale factor in tecnai.py, you should copy the value to your new installation.

[< How to Update from v2.2 (Linux)](/leginon/Leginon_Manual/Upgrade_Instructions/Upgrade_to_Leginon_System_version_30_from_version_22/How_to_Update_from_v22_Linux)
