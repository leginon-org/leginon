# Upgrade processing server

## Download myami-beta source code

    git clone -b myami-3.3 http://emg.nysbc.org/git/myami myami-3.3

## Install Appion/Leginon Packages

### Install all the myami python packages *except appion* using the following script:

    cd /your_download_area
    cd myami-3.3
    sudo ./pysetup.sh install

That will install each package, and report any failures. To determine the cause of failure, see the generated log file "pysetup.log". If necessary, you can enter a specific package directory and run the python setup command manually. For example, if sinedon failed to install, you can try again like this:

    cd sinedon
    sudo python setup.py install

### Move leginon.cfg/instruments.cfg/sinedon.cfg if it was saved with the old installation. In general, the installation would have put it in /etc/myami. Therefore, you do not have to do anything.

Run this script to find out where it was:

     
    cd /your_download_area/myami/leginon/
    ./configcheck.py


If the script can not find leginon.cfg, and you found a copy of leginon.cfg in $PYTHONSITEPKG/leginon/config from the last installation, move that leginon.cfg to $PYTHONSITEPKG/leginon.

> **Note:** See external reference `Appion:Run Database Update Script`

# Upgrade web server

Rename your current myamiweb at the document root of the web server to something else as a backup.

## install the 3.3 version of pyami as it is done on processing server.

### restart redux server

## Install updated Web viewers and tools

See [Install the Web Interface](/leginon/Leginon_Manual/Complete_Installation/Web_Server_Installation/Install_the_Web_Interface) section in Complete Installation Chapter to put the new myamiweb tools to document root for the web server. There is no need to run WebToolSetupWizard, however. See below.

## Copy config.php from your older myamiweb backup to the new myamiweb.

## Import new versions of Leginon Applications

Old version of MSI Leginon applications will still run but without new feature. Use the Web administrator tool to import new version as shown in [Steps involved in the installation](/leginon/Leginon_Manual/Administration_Tools/Steps_involved_in_the_installation) Step for "Import Applications".

[How to Update from v3.2 (Instrument Computer) >](/leginon/Leginon_Manual/How_to_Update_from_v32_Instrument_Windows_Computer)
