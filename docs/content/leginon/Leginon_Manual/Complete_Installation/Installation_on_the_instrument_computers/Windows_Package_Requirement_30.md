# General

## You Will need internet access to get these:


You should generally be able to use the most recent versions of these packages that are available from their respective web sites. Just be sure to always get the version that is compatible with Python 2.7. However, you must use the exact version for numpy. If you are having trouble with the most recent version, try to use the specific versions we include in http://emg.nysbc.org/redmine/projects/leginon/files

------------------------------------------------------------------------

Program package web site local copy of win32 installer local copy of amd64 installer
Python > 2.7.10 <http://www.python.org> python-2.7.16.msi python-2.7.18.amd64.msi
wxPython 2.8 or newer <http://www.wxpython.org> wxPython2.8-win32-unicode-2.8.12.1-py27.exe wxPython2.8-win64-unicode-2.8.12.1-py27.exe
MySQL Python client 1.2 or newer <http://sourceforge.net/projects/mysql-python> MySQL-python-1.2.4b4.win32-py2.7.exe MySQL-python-1.2.3.win-amd64-py2.7.exe
Python Imaging Library (PIL) 1.1.4 or newer <http://www.pythonware.com/products/pil/> PIL-1.1.7.win32-py2.7.exe PIL-fork-1.1.7.win-amd64-py2.7.exe
NumPy (use only from our file to match compiled numextension numpy-1.7.0-win32-python2.7.exe numpy-MKL-1.6.2.win-amd64-py2.7.exe
SciPy 0.5.1 or newer <http://www.scipy.org> scipy-0.11.0-win32-superpack-python2.7.exe scipy-0.11.0.win-amd64-py2.7.exe
---------------------------------------------------------------------------------------------------- ------------------------------------------------------------------------------------------------------------------------------ --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Use pyMySQL for leginon 3.6 and above instead of MySQL Python client for both win32 and 64.
\|pyMySQL 0.10.1 (not higher)\|https://pypi.org/project/PyMySQL/\|pyMySQL-0.10.1-py2.py3-none-any.whl

## (trunk, beta, 3.3 and up) GIT client used for check out from our repository

We have switched to git revision control recently. If you want to install the newest changes, you need to use the files from git repository.

You can clone our repository with

Name: Download site:
------------------------------------- ----------------------------------------------------------------------------------
git for Windows <https://git-for-windows.github.io>

- During the installation, select "Checkout as-is, commit as-is" option at the step regarding automated translation of CRLF and LF line endings if you are a developer and may commit changes.
- Default is fine with the rest of the options.

1.  Packages from NRAMM

Most of the subpackages from NRAMM are obtained through our repository. You have two option depending on your situation

1. [Clone from git repository (newer version)](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Windows_General_Package_Requirement#Cloning-myami-git-repository)
2. Copy your git clone or svn checkout from your linux box if you do not have internet access on instrument PC.

## Cloning myami git repository

We recommend using git bash to do so which gives most freedom in configuration and so that you can use unix syntax.
[git for windows cloning](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Windows_General_Package_Requirement/Git_for_windows_cloning)

- Right Click at the folder where it will contain your clone and choose "Git Bash Here" to start the shell window.

- With Windows XP "Git Bash Here" does not appear with right-click. In this case, you can start git bash from **Start menu/Programs/Git/Git Bash** and move the folder created to where you want it to be.

### To checkout (called clone in git) the package from NRAMM:

See [Acquiring NRAMM Repository files](/leginon/Download_Appion_Files) for different examples and match the repository with what you do on the Linux side.

## numextension windows installer

Because numextension and would require extra compilers if you build them yourself, we have created Windows installers for them for python 2.7 and made them available at /redmine/projects/leginon/files.

## These are the current Leginon python 2.7 compiled packages you should install by opening them on Windows.

Package win32 amd64
------------------------------- --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
numextension numextension-svn.win32-py2.7-numpy1.7.0.exe numextension-svn.win-amd64-py2.7-numpy1.6.2.exe

[Windows Installation That apply to all instruments >](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Windows_Installation_All)


# Additional Requirement on the microscope


## FEI Tecnai/Titan

------------------------------------------------------------------------

TEM Scripting or Tecnai Scripting Request this when purchasing the microscope Required
Low Dose Server Library Should come with the microscope if low dose kit was purchased Required only if you want to use low dose kit with Leginon's Manual Application
Advanced TEM Scripting Request this when purchasing the microscope Required if you have Selectris or Falcon Camera
---------------------------------------------------- ---------------------------------------------------------------------------------------------- -------------------------------------------------------------------------------------------------------------------------

## JEOL

Depending on setup. See [JEOL External3 setup](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_microscope_computer_30/JEOLCOM_installation_specifics/JEOL_External3_setup)


# Additional Requirement for cameras


## Gatan camera controlled by Digital Micrograph installed on FEI Tecnai/Titan microscope computer.

program/package notes
------------------------- ----------
TecnaiCCD.dll

------------------------------------------------------------------------

Program package web site local copy of win32 installer
comtypes 0.6.2 [http://sourceforge.net/projects/comtypes](http://sourceforge.net/projects/comtypes/files/comtypes/0.6.2/comtypes-0.6.2.win32.exe") comtypes-0.6.2.win32.exe
------------------------------------ ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Gatan K2/K3 camera and its associated Orius camera controlled by Digital Micrograph installed on stand-alone 64-bit computer.

SerialEM DigitalMicrograph Plug-in. Get only what you need for your Digital Micrograph version.

------------------------------------------------------------------------

DM version local copy of SerialEM SEMCCD description
2.2.x SEMCCD-GMS2-64.dll DM for 64-bit GMS 2.0 - 2.2
2.3.0 SEMCCD-GMS2.30-64.dll DM for 64-bit GMS 2.30
2.3.1, 2.3.2, 3.0 SEMCCD-GMS2.31-64.dll DM for 64-bit GMS 2.31 and above
3.31 and above SEMCCD-GMS3.31-64.dll DM for 64-bit GMS 3.31 and above
------------------------------------------ ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ ----------------------------------------------------------------------------

Note: DM = Digital Micrograph; GMS = Gatan Microscopy Suite
32bit versions also exit, but not for GMS 2.31 and above

## TIA-controlled camera (FEI Eagle, FEI Falcon, and Gatan Orius used with Falcon

program/package notes
------------------------- ----------------------------------------------------
Tia.dll (Should come with the microscope)

------------------------------------------------------------------------

Program package web site local copy of win32 installer
comtypes 0.6.2 [http://sourceforge.net/projects/comtypes](http://sourceforge.net/projects/comtypes/files/comtypes/0.6.2/comtypes-0.6.2.win32.exe") comtypes-0.6.2.win32.exe
------------------------------------ ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Tietz camera

program/package local win32 installer
------------------------------------------------------------ ----------------------------------------------------------------------------------------------------------------------------------------------
Python for Windows extension (pywin32) pywin32-218.win32-py2.7.exe

program/package notes
------------------------- ----------------------------------------------
CAMC4.exe (Should come with the camera)

## Direct Electron camera

program/package notes
---------------------------------------------------------------------------------- ----------------------------------------------------------------
DirectElectronAPI.exe (Should come with the camera)
[Google protobuf](http://code.google.com/p/protobuf/) [portobuf installation instruction](/leginon/portobuf_installation_instruction)

## Film (Only for FEI Tecnai/Titan)

program/package notes
------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
adaexp.exe This is the exposure adaptor. Contact Max Otten: mto@feico.com and request for adaexp.exe that works with your version of Tecnai user interface program.



[Installation >](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Windows_Installation_All)
