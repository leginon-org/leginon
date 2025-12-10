## Download myami 2.1.x source code

> **Note:** See external reference `appion:Download_Appion_Files_Shared`

## Install Appion/Leginon Packages

### Install all the myami python packages *except appion* using the following script:

    cd /your_download_area
    cd myami
    sudo ./pysetup.sh install

That will install each package, and report any failures. To determine the cause of failure, see the generated log file "pysetup.log". If necessary, you can enter a specific package directory and run the python setup command manually. For example, if sinedon failed to install, you can try again like this:

    cd sinedon
    sudo python setup.py install

## Rename your current myamiweb at the document root of the web server to something else as a backup.

## Install updated Web viewers and tools

**You will not need to upgrade php mrc tools**.

See [Install the Web Interface](/leginon/Leginon_Manual/Complete_Installation/Web_Server_Installation/Install_the_Web_Interface) section in Complete Installation Chapter to put the new myamiweb tools to document root for the web server.

## Copy config.php from your older myamiweb backup to the new myamiweb folder.

## Step through setup wizard in the myamiweb on your server

The Setup Wizard will take you through the steps to update config.php If the wizard does not have the privilege to modify the file at the last step, copy the displayed result to an text editor and save as config.php to replace the olde one.

You will be asked about whether you want to enable myamiweb user login feature that restricts individual user's access to projects and administrator features. Read about it [here](/leginon/appionUser_Management)

> **Note:** See external reference `Appion:Run Database Update Script`

[How to Update from v2.0 (Microscope Windows Computer) >](/leginon/Leginon_Manual/Upgrade_Instructions/Upgrade_to_Leginon_System_version_21_from_version_20/How_to_Update_from_v20_Microscope_Windows_Computer)
