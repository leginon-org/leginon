Next Leginon/Appion release web image viewer will not be compatible with CentOS 5 due to prerequisites of REDUX, the new image server that is compatible with php 5.3 used in modern os. The Leginon processing server code is still compatible with python 2.4 which came with CentOS 5 but the development from now on will assume python version 2.6 along with other default yum installed packages of CentOS 6.

# How to Update from v2.2 (Linux)

## Upgrade OS of the web server to CentOS 6 if you are upgrading from the non-redux version of myami 2.2

Other OS with php 5.3 and above should also work but we can't provide instruction for all individual cases.

1.  Preliminary document for Ubuntu [Myami on Ubuntu](/leginon/Myami_on_Ubuntu)

## Download myami trunk source code

-   unstable with latest features

 
This contains features that may still be under development. It is not supported and may not be stable. Use at your own risk.

    svn co http://emg.nysbc.org/svn/myami/trunk myami/


**Note:** If you are installing this file on a microscope Windows PC, you may use [Tortoise SVN](http://tortoisesvn.tigris.org/) to checkout the files.

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

> **Note:** See external reference `Appion:Run Database Update Script`

[How to Update from v2.1 (Microscope Windows Computer) >](/leginon/Leginon_Manual/Upgrade_Instructions/Upgrade_to_Leginon_System_version_22_from_version_21/How_to_Update_from_v21_Microscope_Windows_Computer)
