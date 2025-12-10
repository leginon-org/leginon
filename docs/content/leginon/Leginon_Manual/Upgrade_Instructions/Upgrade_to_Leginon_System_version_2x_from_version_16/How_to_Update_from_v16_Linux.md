The changes from v1.6 requires update of all in-house components of Leginon, dbemtools (called myamiweb in the new version) and database
but **not the php mrctools**.

**This processing package upgrade instruction includes that for installing Appion's processing scripts and executables. They have more supporting package requirement. Therefore, if you do not plan to use Appion on this computer, you may skip it.**

Don't forget that you need to also update the packages on the microscope-controlling computer
since the pyScope update need to be synchronized.

See [Installation Troubleshooting](/leginon/Leginon_Manual/Installation_Troubleshooting) and [Leginon Bulletin Board](http://emg.nysbc.org/redmine/projects/leginon/boards) searching
for "install" if you run into problems.

## Check and correct the following before you start, because we did not put in the checks for you, and your upgrade will fail if it is incorrect.

### You must have an administrator user in your database

1.  Go to "http://your_host/dbem_1_5_1/adduser.php
2.  Check to see that you do have a user with "name" ( as in username) as "administrator" (all lower-case). If you don't have one, make one and save it.

### All users should be assigned to a group

1.  Go to "http://your_host/dbem_1_5_1/addgroup.php
2.  Create at least a group and save
3.  Go to "http://your_host/dbem_1_5_1/adduser.php
4.  If you did not have group created before, select each user and choose a group and then click save. If there is only one group that you just created, you will need to click save even though you can not make the group selection.

## Packages required from NRAMM

All Leginon (and Appion) packages distributed from NRAMM are now under one svn control called myami.

A few updates are needed for preparation of python 3.0 compatibility where the method for importing module is changed. They will still run under python 2.4 and up.
Here are the packages you need to install with python installer

  SVN subPackage Name   Reason for update:
  --------------------- -------------------------------------------
  numextension          package import method change
  libcv                 package import method change
  leginon               new features
  pyami                 new features
  sinedon               required for updating database
  pyscope               new method for creating pythoncom modules
  imageviewer           debug

## Download Leginon 2.0 source code (substitute that of newer releases by 2.0 ones)

> **Note:** See external reference `appion:Download_Appion_Files_Shared`

## Perform system check if you can't remember where you have installed your Leginon before.

    cd /your_download_area/myami/leginon
    python syscheck.py

You should have all the supporting packages installed for v1.6. If you see any lines like "* Failed...", then you have something missing. Otherwise, everything should result in "OK".

## Move your existing python processing packages to a backup directory:

At the beginning of the syscheck.py output, the location of the exisiting Leginon folder is shown. Although new installation overwrite the old in most cases, problem has been observed in the past. Therefore, it is best to remove the old files from the path before new installation. Better yet, copy into a backup folder because we need some configuration files from them.

For example, your Leginon folder is at /usr/lib/python/site-packages/Leginon

    cd /usr/lib/python/site-packages
    mkdir Leginon1_6_backup
    mv Leginon Leginon1_6_backup

Be aware that in some cases the installed package name is different (capitalized) from your svn package name and that numextension amd libCV are not in its own subdirectory in the python library but just the compiled .so files

> **Note:** See external reference `appion:Install Appion Packages Shared`

## Copy your Leginon1.6 sinedon.cfg to the new installation

-   Find your sinedon.cfg. Depending on your previous setting, look in the directories listed here in order:
    *your home directory as described in syscheck.py
    *The sinedon directory where it is called from. If unsure, start python command line and type these to find out:
        python> import sinedon
        python> sinedon


-   If sinedon.cfg reside in the installed sinedon subpackage, you should copy it from your Leginon1,6 backup to the new installation.
        cd /your_default_python_installation_path
        cp Leginon_1_6_backup/sinedon/sinedon.cfg sinedon

## Copy your Leginon1.6 leginon.cfg to the new installation similarly

-   Find your leginon.cfg. Depending on your previous setting, look in the directories listed here in order:
    *your home directory as described in syscheck.py
    *The leginon directory where it is called from. If unsure, start python command line and type these to find out:
        python> import leginon
        python> leginon


-   If leginon.cfg reside in the installed leginon subpackage, you should copy it from your Leginon1,6 backup to the new installation.
        cd /your_default_python_installation_path
        cp Leginon_1_6_backup/Leginon/leginon.cfg leginon

## Back up all your databases

**Very Important: Fix the bad tables before backup with mysqldump or the backup would be corrrupted. Sorry, it was our fault a long time ago.**

### Check and Fix your database for bad tables

We've found this on two databases outside NRAMM that there are empty tables created that causes a bad database backup. Please check and correct your database first before your backup.

1.  start mysql command line on your leginondb
        mysql -u usr_object your_leginon_database
2.  display all tables
        mysql> show tables;
3.  if you find both BindngSpecData and bindingspecdata, you have a problem. The former has data in there and the later does not. If you have data in both tables, please contact us. We will need to create a customized solution. You can check like this:
        mysql> select * from BindingSpecData;
        mysql> select * from bindingspecdata;
4.  remove the empty lowercased table
        mysql> drop table bindingspecdata;
5.  repeat 3-4 on launchedapplicationdata and nodespecdata

### Backup

We will be doing a database update that is not backward compatible, Make sure you back up all your current databases before performing the update

-   mysqldump -u usr_object your_leginon_database > leginondb_1_6_backup_today's_date
-   mysqldump -u usr_object your_project_database > projectdb_1_2_backup_today's_date
-   .... do the same to any of your processing databases if you have installed and used Appion 1.0 beta

## Install updated Web viewers and tools

**You will not need to upgrade php mrc tools**.

See [Install the Web Interface](/leginon/Leginon_Manual/Complete_Installation/Web_Server_Installation/Install_the_Web_Interface) section in Complete Installation Chapter to put the new web tools (Now under subpackage myamiweb) to document root for the web server.

## Step through setup wizard in the myamiweb on your server

The Setup Wizard will take you through the steps to create config.php and to create and initialize values for the new tables. For example, project database will contain a table called privileges when you finish. Your old config.php is not formatted correctly for the new viewers but the parameters for databases stands. You can enter them in the wizard.

You will be asked about whether you want to enable myamiweb user login feature that restricts individual user's access to projects and administrator features. Read about it [here](/leginon/appionUser_Management)

## Check and modify your [sinedon.cfg](/leginon/Leginon_Manual/Complete_Installation/Processing_Server_Installation/Configure_sinedoncfg) to be compatible to the new version

All module names are now all in lower cass.

> **Note:** See external reference `Appion:Run Database Update Script`

There should be a least scripts to run.
The first one updates UserData and GroupData so that new data viewing and processing privileges can be enforced
The second is a wide-scale change on database schema many on appion processing databases if you had one, and some on projectdata and leginondata.
The third fills in some appion data that was obtained with slow query in previous versions.
The rest are debug update after the release of 2.0.0.

[How to Update from v1.6 (Microscope Windows Computer) >](/leginon/Leginon_Manual/Upgrade_Instructions/Upgrade_to_Leginon_System_version_2x_from_version_16/How_to_Update_from_v16_Microscope_Windows_Computer)
