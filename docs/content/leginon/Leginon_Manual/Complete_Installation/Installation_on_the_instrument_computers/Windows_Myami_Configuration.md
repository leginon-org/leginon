## Locate global configuration directory following standard on Windows

Saving cfg files in a global location reduces future need for copying old configuration to updated installation. The location is different for different versions of Windows. To locate the one for your Windows version:

1. go to C:\python27\Lib\site-packages\leginon
2. run configcheck.py

The script gives the three search directories of the cfg files and the loaded file if present. Note the first search directory that with a name most likely start with **C:\Programs** and ends with **\myami**. This is the **global configuration directory** we will use.


## Configure leginon.cfg:

Follow the instructions in [Configure leginon.cfg](/leginon/Leginon_Manual/Complete_Installation/Processing_Server_Installation/Configure_leginoncfg) located in the section for Linux installation but note the location of the configuration files follows. In addition, if the storage disk is mapped onto the Windows PC as drive Z, this mapping should be included in leginon.cfg. See below.

-   Configurations for all users and all local copy and installation of leginon (Recommended on the microscope computer since users are not expected to start the main processing here)


`<Global configuration directory>\leginon.cfg


Example:


C:\Program Files\myami\leginon.cfg


-   The skeleton (default) configuration file is available at:


C:\Python27\Lib\site-packages\leginon\leginon.cfg.template


## Configure sinedon.cfg:

Follow instruction in [Configure sinedon.cfg](/leginon/Leginon_Manual/Complete_Installation/Processing_Server_Installation/Configure_sinedoncfg) in the section for Linux installation but note the location of the configuration files follows.

* (Recommended on microscope computer) For all users, put sinedon.cfg in the **global configuration directory** such as


C:\Program Files\myami\sinedon.cfg


* the skeleton sinedon configuration file is


C:\Python27\Lib\site-packages\sinedon\examples\sinedon.cfg


## Configure instruments.cfg:

* A template for instruments.cfg is in the installed pyscope directory as "instruments.cfg.template". Copy it to


C:\Programs\myami\instruments.cfg


-   **Remove the Sim Tem and Sim Cam modules in the configuration**.

You need to configure this according to the instrument you have on the computer.

Read below about the common information for microscope and for multiple cameras

-   Add the modules for your microscope and camera.
    -   If your microscope uses FEI TEM Scripting Interface, youe scope module.class is fei.Tecnai
    -   If you have Direct Electron camera DE12, your camera module.class is de.DE12
    -   If you have a Gatan camera running on the microscope computer that you interface through DigitalMicrograph, your camera module.class is gatan.Gatan
    -   If you have a Gatan K2 Summit running on its only 64-bit computer, your camera module is dmsem and three cameras are added. See [Gatan K2 Installation Notes](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Gatan_K2_Summit_Support/Gatan_K2_Installation_Notes)
    -   If you have a Tietz camera, there are several choices for the "class" field. Run the tietztest.py script that comes in pyscope to tell you your available options.

> **Note:** See [instruments.cfg for 2.2](/leginon/Instrumentscfg_for_22)

The file contains other examples of microscope and camera drivers that we distribute from NRAMM.

[< Installation](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Windows_Installation_All) | [Additional installation specific to the microscope >](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_microscope_computer_30)
