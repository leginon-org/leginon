We recommend that you use git pull to get minor update files

simply change directories to your download area inside your myami git clone and run

    git pull

.

*NOTE: On CentOS6, on the first time you run "git pull", it may complain

    error: Ref refs/remotes/origin/myami-beta is at e48a4bc1ea51b705af53fe11b778aff350f58f88 but expected 213db4b122c39154208ad655727628f42c414f8e
     ! 213db4b..1348e4a  myami-beta      -> origin/myami-beta  (unable to update local ref)

Just repeat the same command until it returns

something like this with number of files changed,

    Updating 207294d..4f7d0e9
    Fast-forward
    .....
     6 files changed, 30 insertions(+), 13 deletions(-)

or

    Already up-to-date.

## Update the Appion Packages


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

    cp -rf myamiweb /var/www/html

## Run Database Update Script

Running the following script will indicate if you need to run any database update scripts.

    cd /your_download_area/myami/dbschema
    python schema_update.py

This will print out a list of commands to paste into a shell which will run database update scripts.
You can re-run schema_update.py at any time to update the list of which scripts still need to be run.
