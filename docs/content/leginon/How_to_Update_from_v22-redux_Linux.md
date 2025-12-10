2.2-redux version is installed on CentOS6 and uses redux. Its upgrade to Leginon/Appion 3.0 release does not require os upgrade.

# Upgrade processing server

## Download myami 3.0 source code

    svn co http://emg.nysbc.org/svn/myami/branches/myami-3.0/

## Install Appion/Leginon Packages

### Install all the myami python packages *except appion* using the following script:

    cd /your_download_area
    cd myami
    sudo ./pysetup.sh install

That will install each package, and report any failures. To determine the cause of failure, see the generated log file "pysetup.log". If necessary, you can enter a specific package directory and run the python setup command manually. For example, if sinedon failed to install, you can try again like this:

    cd sinedon
    sudo python setup.py install

### Move leginon.cfg/instruments.cfg/sinedon.cfg if it was saved with the old installation.

Run this script to find out where it was:

     
    cd /your_download_area/myami/leginion/
    ./configcheck.py


If the script can not find leginon.cfg, and you found a copy of leginon.cfg in $PYTHONSITEPKG/leginon/config from the last installation, move that leginon.cfg to $PYTHONSITEPKG/leginon.

> **Note:** See external reference `Appion:Run Database Update Script`

# Upgrade web server

Rename your current myamiweb at the document root of the web server to something else as a backup.

## install the 3.0 version of redux and pyami.

### Follow [Install Redux image server](/leginon/Leginon_Manual/Complete_Installation/Web_Server_Installation/Install_Redux_image_server) instruction but note the following

-   The old version in python's site-packages directory will be overwritten.
-   The old redux.cfg, if in the installation, is still applicable.
-   Make sure you run fftwsetup.py if you have odd-dimension camera such as Gatan K2.

## Install updated Web viewers and tools

See [Install the Web Interface](/leginon/Leginon_Manual/Complete_Installation/Web_Server_Installation/Install_the_Web_Interface) section in Complete Installation Chapter to put the new myamiweb tools to document root for the web server. There is no need to run WebToolSetupWizard, however. See below.

## Copy config.php from your older myamiweb backup to the new myamiweb.

## Import new versions of Leginon Applications

All MSI Leginon applications need to be upgraded or it will not run. Use the Web administrator tool to do this as shown in [Steps involved in the installation](/leginon/Leginon_Manual/Administration_Tools/Steps_involved_in_the_installation) Step for "Import Applications".

[How to Update from v2.2-redux (Instrument Computer) >](/leginon/Leginon_Manual/Upgrade_Instructions/How_to_Update_from_v22_Instrument_Windows_Computer)
