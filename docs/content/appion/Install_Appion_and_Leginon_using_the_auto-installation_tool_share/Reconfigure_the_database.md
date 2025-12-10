1.  Drop the databases if they exist
     
        mysql -h localhost -u root

        show databases;

    
    If you see:
    _projectdb
    leginondb_
        drop database projectdb;
        drop database leginondb;
2.  Create the databases
        create database projectdb;
        create database leginondb;
3.  [Download config.php](http://emg.nysbc.org/redmine/attachments/503/config.php) and put it in **/var/www/html/myamiweb**
     
4.  Change the permission of the config file
        chmod 777 /var/www/html/myamiweb/config.php
5.  Point your web browser to http://localhost/myamiweb/setup
    1.  The database username is **root**
    2.  There is no database password. Leave this field empty.
    3.  Click **Next** on each page without making any changes.
    4.  Eventually, you will see a button to **Create Web Tools Config**. Click on this button, and ignore the Apache User error.
    5.  Click on the **DB Initialization** button.
    6.  Click **Next**.
    7.  Click **Next** to insert default values.
    8.  You will need to enter information for the Adminstrator Appion user. You may enter any password and your email address.
    9.  When this completes, you may start using Appion, or may continue with the following steps to insert a sample project into the database which can be used for processing with Appion.
         
6.  Delete the sample images folder
        cd /myamiImages/leginon
        rm -rf sample
7.  Point your browser to the following url but first replace **your_root_password** with the root password of your CentOS installation.
        http://localhost/myamiweb/setup/autoInstallSetup.php?password=your_root_password
8.  When this script completes, you will be redirected to the Appion and Leginon home page.
