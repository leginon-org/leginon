## Processing-side Leginon Windows Installation

### Install Python and Support Packages (Note that python 2.5 must be used):

This list does not include pyton XML module because it is included in the python
package for window.

  Name:                                         Download site:
  --------------------------------------------- ------------------------------------------------
  Python 2.5*                                  <http://www.python.org>
  Python for Windows extension (pywin32)        <http://sourceforge.net/projects/pywin32/>
  wxPython 2.5.2.8 or newer                     <http://www.wxpython.org>
  MySQL Python client 1.2 or newer              <http://sourceforge.net/projects/mysql-python>
  Python Imaging Library (PIL) 1.1.4 or newer   <http://www.pythonware.com/products/pil/>
  NumPy 1.0b5 (tested, others may work)         <http://www.scipy.org>
  SciPy 0.5.1 or newer                          <http://www.scipy.org>
  Tortoise SVN client                           <http://tortoisesvn.tigris.org>

*Python 2.5 is the only python version that we have compiled numExtension. libCV and
comarray in. Therefore no other python version works for now.

Execute the installer file and follow the directions.

### Packages required from NRAMM

These are the packages you will install with the python installer.

  Name:         Purpose:
  ------------- -----------------------------------
  leginon       modular TEM image acquisition
  pyami         general functions
  sinedon       Leginon/database interaction
  pyscope       microscope control and monitoring
  imageviewer   image viewing for tomography

Because numextension and libcv requires extra compilers, we have created window
installer for them for python 2.5 and made them available through <http://www.leginon.org/>.

These are the Leginon v2.0 python 2.5 compiled packages installed through python installer on Windows.

  Downloadfile Name                    Installed Python Package File   Purpose:
  ------------------------------------ ------------------------------- ---------------------------------------------------------
  NumExtension-1.2.0.win32-py2.5.exe   numextension.pyd                c extension for numerical processing
  libCV-0.2.win32-py2.5.exe            libCV.pyd                       small c library of algorithm from computer vision field

### Check out SVN Source Files from the depository

Use your mouse to do the following

-   Create Leginon2.0 directory somewhere at your convenience


-   Change directory into Leginon2.0


-   Right-click the mouse botton in this directory window and select Tortoise svn
    Checkout in the menu:
    ![](images/svnmenu.png)


-   Set up svn checkout window like this to check out from /svn/myami/trunk to Leginon2.0
    ![](images/svnco.png)

### Install the packages you downloaded from NRAMM svn depository

-   Start a command line Window from Start Menu


-   Install the package in each folder with commands such as
        cd Your_Download_Place\Leginon2.0\leginon
        c:\python25\python.exe setup.py install

### Download the two Window Installer Files from Leginon website

<http://www.leginon.org/>

### Install individual packages

Excute the installer files and follow the instruction.

### Mapping Drives:

If you plan to run Leginon directly on the Windows machine, such as in [Configuration C](/leginon/Leginon_Manual/Complete_Installation/Possible_Computer_Set-up_Configurations#Configuration-C), and your data files are served through a Samba server on a Linux machine, you will need to map the network drive. For example, if your Samba server has a hostname your_smbserver, and you have set up a share called [your_share_point] which points to /your_data_path/ and leginon data will be saved under a folder in /your_data_path/leginon/.

-   Start, My Computer


-   Tools menu, Map network drive


-   Use an unmapped drive such as Z:

Enter shared path in Windows format
as


\your_smbserver\your_share_point


* Add the drive and the Linux path to leginon.cfg on the Windows machine
as


[Drive Mapping]
Z:/your_data_path


* Add image path to leginon.cfg on the Windows machine in Linux format
as


[Images]
path:/your_data_path/leginon


### Configure leginon.cfg:

Follow the instructions in [Configure leginon.cfg](/leginon/Leginon_Manual/Complete_Installation/Processing_Server_Installation/Configure_leginoncfg) located in
the section for Linux installation but note the location of the configuration files
follows. In addition, if the storage disk is mapped onto the Windows PC as drive Z, this
mapping should be included in leginon.cfg. See above.

-   Configurations for all users


`<Python directory>\Lib\site-packages\Leginon\config\leginon.cfg


Example:


C:\Python25\Lib\site-packages\Leginon\config\leginon.cfg


-   Configurations for individual users


`<Home directory>\leginon.cfg


Example:


C:\Documents and Settings\Leginon User\leginon.cfg


-   A skeleton (default) configuration file is available:


C:\Python25\Lib\site-packages\Leginon\config\default.cfg


### Configure sinedon.cfg:

Sinedon is designed to be able to interact with multiple databases.

Follow instruction in [Configure sinedon.cfg](/leginon/Leginon_Manual/Complete_Installation/Processing_Server_Installation/Configure_sinedoncfg) in
the section for Linux installation but note the location of the configuration files
follows.

* For all users, put sinedon.cfg with the installed package as


C:\Python25\Lib\site-packages\sinedon\sinedon.cfg


* Your home directory on Windows:


C:\Documents and Settings\your_name>


* the skeleton sinedon configuration file is


C:\Python25\Lib\site-packages\sinedon\examples\sinedon.cfg


### Create Leginon and Leginon Client shortcut in Start menu menu under Leginon

This instruction applies to Windows XP.

* Go to C:\Documents and Settings\All Users\Start Menu\Programs\ and create a new
folder named Leginon.

* In another window, go to


C:\Python25\Lib\site-packages\leginon


* Create a shortcut from start-leginon.py as Leginon and a shortcut from launcher.py as Leginon Client.

* Move the two shortcuts into


C:\Documents and Settings\All Users\Start Menu\Programs\Leginon


### Additional Software (Optional):

TigerVNC (http://tigervnc.org/) --- allows remote access to windows screen. If you get tired of going into the microscope room just to open the column valves.

## Database server Windows Installation

### We do not do this at NRAMM. Please follow the instruction in Linux installation and modify it for Windows at your own risk.

For a good Windows specific instruction for general PHP configuration with MySQL for
Apache 2 in Windows, try http://www.artfulsoftware.com/php_mysql_win.html.

[< Web Server Installation](/leginon/Leginon_Manual/Complete_Installation/Web_Server_Installation) | [Additional installation on the microscope computer >](/leginon/Additional_installation_on_the_microscope_computer)
