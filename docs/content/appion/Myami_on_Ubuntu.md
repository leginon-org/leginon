***WARNING: This is a preliminary document. Use at your own risk!***

# myami on Ubuntu

This is mainly a log of various experiences installing myami on Ubuntu which will gradually evolve into a more formal document. This will attempt to demonstrate the installation of all of myami including both leginon and appion on a single Ubuntu host. This will also include running MySQL, Apache Torque, etc. on this local host without needing to connect to any other host.

## Installing a basic Ubuntu system

We use Ubuntu 12.04 LTS (Precise) Desktop 64 bit. Install a basic system from an image on CD or bootable USB drive. Default selections during the install process, no 3rd party repositories, no network configuration and no updates during the installation. This makes it easier in the remainder of this document to know that we have started from a known base system. Reboot.

Following the initial reboot:

* connect to the internet (click network icon in upper right)

* update packages:

    sudo apt-get update
    sudo apt-get upgrade

-   Reboot

You now have a basic up-to-date Ubuntu system

## Installing additional packages required by myami

There are many additional packages to install, but we can try to condense that list to the smallest set necessary to pass to the update command which will then figure out all the other dependencies.

Here is a single command to install all the necessary packages:

    sudo apt-get install subversion vim python-MySQLdb python-wxgtk2.8 python-fs mysql-server php5 php5-mysql libssh2-php php5-gd

During installation, you will be prompted several times to create a mysql root password. This can optionally be left blank at the expense of less security. Note: installing the vim text editor is my own preference... use an inferior text editor if you wish :)

The Scipy package is also required, but the current version 0.9.0 that comes with Ubuntu 12.04 is broken. You need to grab the more recent version of Scipy from Ubuntu Quantal (development version). To make a clean installation that will not confuse the package manager we have prepared a mini-repository that includes this new scipy. You can download and install scipy using the following set of commands copied into your terminal.

    sudo mkdir /usr/local/share/myami

That should get your password in the sudo cache so you can copy the rest of these without entering a password:

    cd /usr/local/share/myami
    sudo wget http://emg.nysbc.org/redmine/attachments/download/1488/ubuntu-scipy-0.10.1.tar.bz
    sudo tar jxf ubuntu-scipy-0.10.1.tar.bz
    sudo sh -c 'echo "deb file:///usr/local/share/myami/ubuntu-scipy-0.10.1 ./" > /etc/apt/sources.list.d/myami.list'
    sudo apt-get update
    sudo apt-get install python-scipy

Make sure that last line executes (may have to hit enter). Also, you may have to confirm installing it without authentication.

## Setting up MySQL databases

-   change bind-address in /etc/mysql/my.cnf to your mysql server address
        #bind-address = 127.0.0.1
        bind-address = your.fixed.ip.address

* create /etc/mysql/conf.d/myami.cnf with the following contents:

    [mysqld]
    default-storage-engine=myisam
    query_cache_size = 100M
    query_cache_limit = 100M

* restart mysql server:

    sudo service mysql restart

* create databases:

    sudo mysqladmin create leginondb
    sudo mysqladmin create projectdb

* create user and grand privileges... login to mysql as root:

    mysql -u root mysql

once inside mysql client, grant privs:

    create user usr_object@'localhost';
    grant all privileges on leginondb.* to usr_object@'localhost';
    grant all privileges on projectdb.* to usr_object@'localhost';
    grant alter, create, insert, select, update on `ap%`.* to usr_object@localhost;

## Setting up Apache web server

create /etc/php5/conf.d/myami.ini with the following contents:

    error_reporting = E_ALL & ~E_NOTICE & ~E_WARNING & ~E_DEPRECATED
    display_errors = On
    register_argc_argv = On
    short_open_tag = On
    max_execution_time = 300
    max_input_time = 300
    memory_limit = 256M

restart apache:

    sudo service apache2 restart

## Install myami

* check out a sandbox from the subversion repository. Note: Minimal branch you should use is myami-2.2-redux. You may use trunk which is generally unstable and untested but most up to date. Use at your own risk!:

    cd
    svn co http://emg.nysbc.org/svn/myami/branches/myami-2.2-redux myami-2.2-redux

* install myami python packages:

    cd myami-2.2-redux
    sudo ./pysetup.sh install
    ADD APPION PYTHON PACKAGE INSTALL HERE

* create image storage directory:

    sudo mkdir /data
    sudo mkdir /data/leginon
    sudo chmod a+w /data/leginon

* configure python packages:

    cp leginon/leginon.cfg.template ~/leginon.cfg
    cp sinedon/examples/sinedon.cfg ~/sinedon.cfg
    cp pyscope/instruments.cfg.template ~/instruments.cfg

then edit and config all three of the above files.

* Install myamiweb:

    sudo cp -r myamiweb /var/www
    sudo chmod 777 /var/www/myamiweb

* setup and configure redux:

    sudo mkdir /var/cache/myami
    sudo mkdir /var/cache/myami/redux
    sudo chown -R www-data.www-data /var/cache/myami
    sudo vim /usr/local/lib/python2.7/dist-packages/redux/pipeline.py

(set cache path and size)

* initialize databases and generate config.php using web tool: http://localhost/myamiweb/setup

* make any manual fixes to /var/www/myamiweb/config.php, such as enable redux cache, disable regular cache...

* Other administrative setup:

http://localhost/myamiweb/admin.php

* add user

* import apps

http://localhost/myamiweb/project/project.php

* add new project

* test if leginon starts:

    start-leginon.py

## Optional additions

* for mounting external network shares

install nfs-common

    sudo apt-get install nfs-common

For automounting and similar services install NIS:

    sudo apt-get install nis
