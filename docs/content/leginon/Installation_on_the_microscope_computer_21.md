# Installation on the microscope computer

[Installation on the microscope computer](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_microscope_computer)

Only processing-side of Leginon system is needed

# Package requirement

## Python and Support Packages (Note that python 2.5 must be used):

This list does not include the python XML module because it is included in the python package for Windows. You should generally be able to use the most recent versions of these packages that are available from their respective web sites. Just be sure to always get the version that is compatible with Python 2.5. If you are having trouble with the most recent version, try to use the specific versions listed here:

  --------------------------------------------- ------------------------------------------------ -----------------------------------------------------
  Python 2.5*                                  <http://www.python.org>                          
  Python for Windows extension (pywin32)        <http://sourceforge.net/projects/pywin32/>       
  wxPython 2.5.2.8 or newer                     <http://www.wxpython.org>                        
  MySQL Python client 1.2 or newer              <http://sourceforge.net/projects/mysql-python>   1.2.3 doesn't have window installer, yet, use 1.2.2
  Python Imaging Library (PIL) 1.1.4 or newer   <http://www.pythonware.com/products/pil/>        
  NumPy 1.0b5 (tested, others may work)         <http://www.scipy.org>                           
  SciPy 0.5.1 or newer                          <http://www.scipy.org>                           
  --------------------------------------------- ------------------------------------------------ -----------------------------------------------------

*Python 2.5 is the only python version that we have compiled numExtension. libCV and comarray in. Therefore no other python version works for now.

## SVN client used for check out from our repository

This required for following this instruction. We have used Tortois SVN client. Alternatively, you may copy the required NRAMM source files from another computer.

  Name:                 Download site:
  --------------------- ---------------------------------
  Tortoise SVN client   <http://tortoisesvn.tigris.org>

## Required supporting programs for the CCD camera from camera makers

Install and register the following programs for CCD cameras from the two makes. Most likely, you already have these installed when the camera and TEM software was installed:

  Camera Make:   File:
  -------------- ---------------
  Gatan          TecnaiCCD.dll
  Tietz          CAMC4.exe*

**Note:** We have experienced slowness of the CAMC4.exe comes with later version Tecnai TUI/TIA. Replacing it with an earlier version of CAMC4.exe resolved the problem

## Supporting programs for film exposure

Install the following if you need film exposure on FEI Tecnai TEM through Leginon, available through FEI. Please contact Max Otten: mto@feico.com and request for adaexp.exe that works with your version of Tecnai user interface program.

  Name:              File:
  ------------------ ------------
  exposure adaptor   adaexp.exe

## Packages required from NRAMM

### These are the sub-packages of myami that you will install with the python installer.

  Name:         Purpose:
  ------------- -----------------------------------
  leginon       modular TEM image acquisition
  pyami         general functions
  sinedon       Leginon/database interaction
  pyscope       microscope control and monitoring
  imageviewer   image viewing for tomography

*For FEI Eagle Camera or Gatan Camera that uses TIA, comarray package needs to be install with python
*[Special Instructions for FEI Eagle Camera](/leginon/Special_Instructions_for_FEI_Eagle_Camera)

Because numextension, comarray and libcv would require extra compilers if you build them yourself, we have created Windows installers for them for python 2.5 and made them available at http://emg.nysbc.org/redmine/projects/leginon/files.

### These are the Leginon v2.0 python 2.5 compiled packages installed through python installer on Windows. Leginon v2.1 uses the same files.

  Downloadfile Name                    Purpose:
  ------------------------------------ ---------------------------------------------------------
  numextension-2.0.0.win32-py2.5.exe   c extension for numerical processing
  comarray-2.0.0.win32-py2.5.exe       com module output conversion to array
  libCV-0.2.win32-py2.5.exe            small c library of algorithm from computer vision field

# Installation

## 1. Register TecnaiCCD.dll, CAMC4.exe (For Tietz camera), and adaexep.exe (For film exposure)

-   For example, from the command prompt:
        adaexp.exe /regserver

## Install Python and supporting packages with their installers

Excute the installer files and follow the instructions.

## 2. Install the Windows Installer Files from Leginon website http://emg.nysbc.org/redmine/projects/leginon/files

Execute the installer files and follow the instructions. **Do not execute comarray-2.0.0.win32-py2.5.3x3 if your camera uses TIA**. See earlier section above.

## 3. Check out SVN Source Files from the repository

Use your mouse to do the following

-   Create Leginon2.1 directory somewhere at your convenience


-   Change directory into Leginon2.1


-   Right-click the mouse botton in this directory window and select Tortoise svn
    Checkout in the menu:
    ![](images/svnmenu.png)


-   Set up svn checkout window like this to check out from http://emg.nysbc.org/svn/myami/branches/myami-2.1 to Leginon2.1
    ![](images/svnco.png)

## 4. Install the packages you downloaded from NRAMM svn repository

-   Start a command line Window from Start Menu


-   Install the package in each folder with commands such as
        cd Your_Download_Place\Leginon2.1\leginon
        c:\python25\python.exe setup.py install

    
    Then continue with the other packages, replacing leginon with the package name. See "These are the sub-packages of myami that you will install with the python installer." section above for complete list.

## 5. Run updatecom.py

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


The output is of course depending on what is available on your microscope computer. You should have either "Tecnai Scripting" or the pairing of "TEM Scripting" and "TOM Moniker".

You will only find Tecnai Exposure Adaptor (Scripting for film exposure) if you ask FEI for it.

The script should generate a few files in C:\python25\Lib\win32com\gen_py with seemly scrambled names such as BC0A2B03-19FF-11D3-AE00-00A024CBA50Cx0x1x9.py

## 6. Configure leginon.cfg:

Follow the instructions in [Configure leginon.cfg](/leginon/Leginon_Manual/Complete_Installation/Processing_Server_Installation/Configure_leginoncfg) located in the section for Linux installation but note the location of the configuration files follows. In addition, if the storage disk is mapped onto the Windows PC as drive Z, this mapping should be included in leginon.cfg. See below.

-   Configurations for all users (Recommended on the microscope computer since users are not expected to start the main processing here)


`<Python directory>\Lib\site-packages\leginon\config\leginon.cfg


Example:


C:\Python25\Lib\site-packages\leginon\config\leginon.cfg


-   The skeleton (default) configuration file is available at:


C:\Python25\Lib\site-packages\leginon\config\default.cfg


## 7. Configure sinedon.cfg:

Follow instruction in [Configure sinedon.cfg](/leginon/Leginon_Manual/Complete_Installation/Processing_Server_Installation/Configure_sinedoncfg) in the section for Linux installation but note the location of the configuration files follows.

* (Recommanded on microscope computer) For all users, put sinedon.cfg with the installed package as


C:\Python25\Lib\site-packages\sinedon\sinedon.cfg


* Your home directory on Windows:


C:\Documents and Settings\your_name>


* the skeleton sinedon configuration file is


C:\Python25\Lib\site-packages\sinedon\examples\sinedon.cfg


## 8. Configure instruments.cfg:

-   A template for instruments.cfg is in the installed pyscope directory as "instruments.cfg.template". Copy it to "instruments.cfg".


-   Remove the Sim Tem and Sim Cam modules in the configuration.


-   Add the modules for your microscope and camera. If you have a Tietz camera, there are several choices for the "class" field. Run the tietztest.py script that comes in pyscope to tell you your available options. For example, if your microscope uses Tecnai Scripting Interface and you have a Gatan camera that you interface through DigitalMicrograph:

> **Note:** See [instruments.cfg for 2.1](/leginon/Instrumentscfg_for_21)
[2.2 release needs additional configuration](/leginon/Instrumentscfg_for_22)

The file contains other examples of microscope and camera drivers that we distribute from NRAMM.

## 9. Additional setup on Tietz cameras

Register the Tietz ping callback function. From a command line window:

    cd C:\python25\Lib\Site-Packages\pyscope
    C:\python25\python.exe tietzping.py

## 10. For strange dimension cameras


Some Tietz camera dimensions are slightly larger than a standard size, for example, 2084 x 2084 instead of the standard 2048 x 2048. Some software will have trouble dealing with these dimensions. It is recommended to force the camera to the lower standard size (some multiple of 2^n). Modify the function that gets camera dimension in tietz.py, gatan.py, or tia.py depending on which camera you are using.

- Go to C:\Python25\Lib\site-packages\pyScope

- Edit tietz.py, gatan.py, or tia.py with a plain text editor

- Find the function "getCameraSize" and replace its contents to force it to return a "hard coded" size. For example:

def getCameraSize(self):
return {'x': 2048, 'y': 2048}


## 11. Create Leginon Admin and Leginon Client shortcut in Start menu menu under Leginon

This instruction applies to Windows XP.

* Go to C:\Documents and Settings\All Users\Start Menu\Programs\ and create a new
folder named Leginon.

* In another window, go to


C:\Python25\Lib\site-packages\leginon


* Create a shortcut from start-leginon.py as "Leginon Admin" and a shortcut from launcher.py as "Leginon Client".

* Move the two shortcuts into


C:\Documents and Settings\All Users\Start Menu\Programs\Leginon


## 12. Mapping Drives (Optional):

Although we don't recommend it, it is possible to run minimal Leginon directly on the Windows machine, Since the database and web servers are not there, you probably will be saving the images through a Samba server on a network drive also available to the Linux machine. If you do so, you will need to map the network drive. For example, if your Samba server has a hostname your_smbserver, and you have set up a share called [your_share_point] which points to /your_data_path/ and leginon data will be saved under a folder in /your_data_path/leginon/.

-   Start, My Computer


-   Tools menu, Map network drive


-   Use an unmapped drive such as Z:

Enter shared path in Windows format as


\your_smbserver\your_share_point


* Add the drive and the Linux path to leginon.cfg on the Windows machine as


[Drive Mapping]
Z:/your_data_path


* Add image path to leginon.cfg on the Windows machine in Linux format as


[Images]
path:/your_data_path/leginon


## Additional Software (Optional):

TigerVNC (http://tigervnc.org/) --- allows remote access to windows screen. If you get tired of going into the microscope room just to open the column valves.

[< Additional Database Server Setup](/leginon/Leginon_Manual/Complete_Installation/Additional_Database_Server_Setup_after_Web_Server_Installation) | [Steps needed for Installation Using Database Administration Tools >](/leginon/Leginon_Manual/Administration_Tools/Steps_involved_in_the_installation)
