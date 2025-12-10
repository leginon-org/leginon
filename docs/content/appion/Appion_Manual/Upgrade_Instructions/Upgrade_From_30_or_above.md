## Download myami 3.x source code


Download myami (contains Appion and Leginon) using one of the following options:

## Option 1: 3.4 version (Current release)

- We have switched to git for version control.
git clone -b myami-3.4 https://emg.nysbc.org/git/myami myami


**Note:** If you are installing these files on a microscope Windows PC, you may use [Git for Windows](https://git-for-windows.github.io) to clone the files. See notes on configuration note in [Here](/appion/LeginonWindows_Package_Requirement_30) Check compatibility as newer version does not support Windows XP.

## Option 2: beta-release version (Used and updated at NRAMM daily with newest features that may not yet documented)

- We have switched to git for version control.
git clone -b myami-beta https://emg.nysbc.org/git/myami myami


**Note:** If you are installing these files on a microscope Windows PC, you may use [Git for Windows](https://git-for-windows.github.io) to clone the files. See notes on configuration note in [Here](/appion/LeginonWindows_Package_Requirement_30) Check compatibility as newer version does not support Windows XP.

## Option 3: Development version (For true developer to play with)

- We have switched to git for version control recently. trunk and future release branches will be available with git clone
- unstable with latest features

 
This contains features that may still be under development. It is not supported and may not be stable. Use at your own risk.

git clone -b trunk https://your_redmine_username@emg.nysbc.org/git/myami myami

- your_redmine_username is required if you intend and have permission to push changes to our repository. Please ask the development team if you would like to contribute.*

**Note:** If you are installing these files on a microscope Windows PC, you may use [Git for Windows](https://git-for-windows.github.io) to clone the files. See notes on configuration note in [Here](/appion/LeginonWindows_Package_Requirement_30) Check compatibility as newer version does not support Windows XP.


## Install Appion Packages


### Install all the myami python packages **except appion** using the following script:

cd /your_download_area/myami
sudo ./pysetup.sh install

That will install each package, and report any failures. To determine the cause of failure, see the generated log file "pysetup.log". If necessary, you can enter a specific package directory and run the python setup command manually. For example, if sinedon failed to install, you can try again like this:

cd /your_download_area/myami/sinedon
sudo python setup.py install

### Install the Appion python package

**Important:** You need to install the current version of Appion packages to the **same location** that you installed the previous version of Appion packages. You may have used a flag shown below (----install-scripts=/usr/local/bin) in your original installation. If you did, you need to use it this time as well. You can check if you installed your packages there by browsing to /usr/local/bin and looking for ApDogPicker.py. If the file is there, you should use the flag. if the file is not there, you should remove the flag from the command to install Appion to the default location.

The pysetup.py script above did not install the appion package. Since the appion package includes many executable scripts, it is important that you know where they are being installed. To prevent cluttering up the /usr/bin directory, you can specify an alternative path, typically /usr/local/bin, or a directory of your choice that you will later add to your PATH environment variable. Install appion like this:

cd /your_download_area/myami/appion
sudo python setup.py install ---install-scripts=/usr/local/bin


## Update the web interface

Copy the entire myamiweb folder found at myami/myamiweb to your web directory (ex. /var/www/html). You may want to save a copy of your old myamiweb directory first.

## Install the Redux Image Server

## Update configuration files

1.  Move your leginon.cfg file
    1.  Ensure you have a leginon.cfg file in the proper location per these [Leginon config instructions](/appion/appionConfigure_leginoncfg)
2.  [Add a .appion.cfg file](/appion/appionConfigure_appioncfg)
3.  Ensure your config.php file is up to date on the web server per these [config.php instructions](/appion/appionInstall_the_Web_Interface_Advanced)


## Run Database Update Script

Running the following script will indicate if you need to run any database update scripts.

cd /your_download_area/myami/dbschema
python schema_update.py

This will print out a list of commands to paste into a shell which will run database update scripts.
You can re-run schema_update.py at any time to update the list of which scripts still need to be run.


## Install new support packages if required:

[New support package requirement for 3.2](/appion/New_support_package_requirement_for_32)
[New support package requirement for 3.3](/appion/Appion_Manual/Upgrade_Instructions/Upgrade_From_30_or_above/New_support_package_requirement_for_33)

_

[Upgrade Instructions ^](/appion/Appion_Manual/Upgrade_Instructions)
