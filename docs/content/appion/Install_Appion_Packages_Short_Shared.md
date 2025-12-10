### Install all the myami python packages *except appion* using the following script:

    cd /your_download_area/myami
    sudo ./pysetup.sh install

That will install each package, and report any failures. To determine the cause of failure, see the generated log file "pysetup.log". If necessary, you can enter a specific package directory and run the python setup command manually. For example, if sinedon failed to install, you can try again like this:

    cd /your_download_area/myami/sinedon
    sudo python setup.py install

### Install the Appion python package

**Important:** You need to install the current version of Appion packages to the **same location** that you installed the previous version of Appion packages. You may have used a flag shown below (---install-scripts=/usr/local/bin) in your original installation. If you did, you need to use it this time as well. You can check if you installed your packages there by browsing to /usr/local/bin and looking for ApDogPicker.py. If the file is there, you should use the flag. if the file is not there, you should remove the flag from the command to install Appion to the default location.

The pysetup.py script above did not install the appion package. Since the appion package includes many executable scripts, it is important that you know where they are being installed. To prevent cluttering up the /usr/bin directory, you can specify an alternative path, typically /usr/local/bin, or a directory of your choice that you will later add to your PATH environment variable. Install appion like this:

    cd /your_download_area/myami/appion
    sudo python setup.py install --install-scripts=/usr/local/bin 
