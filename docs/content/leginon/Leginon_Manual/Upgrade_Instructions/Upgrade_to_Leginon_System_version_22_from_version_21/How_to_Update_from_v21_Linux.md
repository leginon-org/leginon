## Download myami 2.2.x source code

> **Note:** See external reference `appion:Download_Appion_Files_Shared`

## Install Appion/Leginon Packages

### Install all the myami python packages *except appion* using the following script:

    cd /your_download_area
    cd myami
    sudo ./pysetup.sh install

That will install each package, and report any failures. To determine the cause of failure, see the generated log file "pysetup.log". If necessary, you can enter a specific package directory and run the python setup command manually. For example, if sinedon failed to install, you can try again like this:

    cd sinedon
    sudo python setup.py install

### Move leginon.cfg if it was saved with the installation.

Run this script to find out where it was:

     
    cd /your_download_area/myami/leginion/
    ./configcheck.py


If the script can not find leginon.cfg, and you found a copy of leginon.cfg in $PYTHONSITEPKG/leginon/config from the last installation, move that leginon.cfg to $PYTHONSITEPKG/leginon.

## Rename your current myamiweb at the document root of the web server to something else as a backup.

## Install updated Web viewers and tools

**You will not need to upgrade php mrc tools**.

See [Install the Web Interface](/leginon/Leginon_Manual/Complete_Installation/Web_Server_Installation/Install_the_Web_Interface) section in Complete Installation Chapter to put the new myamiweb tools to document root for the web server.

## Copy config.php from your older myamiweb backup to the new myamiweb folder.

## Step through setup wizard in the myamiweb on your server

The Setup Wizard will take you through the steps to update config.php If the wizard does not have the privilege to modify the file at the last step, copy the displayed result to an text editor and save as config.php to replace the olde one.

> **Note:** See external reference `Appion:Run Database Update Script`

## Assigning Cs value for each TEM used by Leginon

schema-r15653.py that shows up in the list of required update when schema-update.py is run is used to assign individual spherical aberration constant (Cs) values to different microscope. Please find out what these values are in advance before running the script to save time.

Running the python script will prompt you at each TEM you have used so far so that you can enter the value in unit of **millimeter**

The Cs value also need to match what is set in pyscope/instrument.cfg before you will be able to acquire more images. See [How to Update from v2.1 (Microscope Windows Computer)](/leginon/Leginon_Manual/Upgrade_Instructions/Upgrade_to_Leginon_System_version_22_from_version_21/How_to_Update_from_v21_Microscope_Windows_Computer)

[How to Update from v2.1 (Microscope Windows Computer) >](/leginon/Leginon_Manual/Upgrade_Instructions/Upgrade_to_Leginon_System_version_22_from_version_21/How_to_Update_from_v21_Microscope_Windows_Computer)
