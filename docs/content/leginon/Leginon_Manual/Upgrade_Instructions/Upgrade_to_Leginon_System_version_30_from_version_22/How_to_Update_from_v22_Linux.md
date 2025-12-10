Leginon/Appion 3.0 release web image viewer will not be compatible with CentOS 5 due to prerequisites of REDUX, the new image server that is compatible with php 5.3 used in modern os. The Leginon processing server code is still compatible with python 2.4 which came with CentOS 5 but the development from now on will assume python version 2.6 along with other default yum installed packages of CentOS 6.

Since this is a major change, if you have an older computer where all parts of Leginon are installed and want to keep the data in the old database, this is a good time to migrate the web server and processing server to a new computer and make the old CentOS 5 computer the dedicate database computer.

# Upgrade database server moving from CentOS 5 to CentOS 6 (non-redux version only)

**If Database server is separate from web server, it can stay at CentOS 5 with MySQL 5.0. You don't need to perform the followings**

If Database server is NOT separated from web server, you will need to export the data and import it back after OS upgrade since CentOS 6 has MySQL 5.1. Direct file copy of the database files will not work.

Repeat the following for leginondb, projectdb, and any processing database that you would like to migrate:

For example, for leginondb:

1. Use mysqldump to create an xml file of the table structure and data (substitute "database_host" with your database server hostname. This assumes that the mysql user "usr_object" has proper privileges for these):

    mysqldump -h database_host -u usr_object -p --extended-insert leginondb > leginondb.sql

2. copy the resulting sql file to a safe place during OS upgrade.

3. After OS upgrade and performing database setup in [Database Server Installation](/leginon/Leginon_Manual/Complete_Installation/Database_Server_Installation)
import that into the empty database ("usr_object" need to have privilages to create table):

    mysql -h database_host -u usr_object -p leginondb < leginondb.sql

# Upgrade web server

## Follow [Complete Web Server Installation](/leginon/Leginon_Manual/Complete_Installation/Web_Server_Installation) including os upgrade to CentOS 6 if you are upgrading from the non-redux version of myami 2.2

Other OS with php 5.3 and above should also work but we can't provide instruction for all individual cases.

1.  Preliminary document for Ubuntu [Myami on Ubuntu](/leginon/Myami_on_Ubuntu)

# Upgrade processing server

## OS upgrade to CentOS 6 upgrade is OPTIONAL for stand-alone processing server

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

[How to Update from v2.2 (Instrument Computer) >](/leginon/Leginon_Manual/Upgrade_Instructions/How_to_Update_from_v22_Instrument_Windows_Computer)
