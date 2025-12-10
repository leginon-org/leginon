[TOC]

## 1 Make sure MySQL is installed

Follow the [installation instructions](/appion/Appion_Manual/Complete_Installation/Database_Server_Installation/).

Also [install phpMyAdmin](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation/Install_phpMyAdmin).
Note that phpMyAdmin version 2.11.10 works with older versions of PHP (that we happen to use).

## 2 Dump tables from cronus4 to a local file

This will grab the actual data that we use so you can play with it.
Log into cronus3 so that you can access cronus4.

    $ ssh cronus3

Use mysqldump to get any table data that you want as in the example below.
Cronus4 is the host.
We do not lock the tables because we don't have permission to.
"project" is the name of the database and "login" is the name of the Table.
We make up a file name for the data to dump to.

    $ mysqldump -h cronus4 -u usr_object --skip-lock-tables --extended-insert project login > ProjectLogin.sql

    mysqldump -h cronus4 -u amber -p --skip-lock-tables --extended-insert project > Project.sql

The `--extended-insert` option causes mysqldump to generate multi-value INSERT commands inside the backup text file which results in the file being smaller and the restore running faster. [ref](http://www.mythtv.org/wiki/Backup_your_database)

More info on mysqldump is [here](http://dev.mysql.com/doc/refman/5.1/en/mysqldump.html#option_mysqldump_tables).

Exit cronus3 when you are done dumping tables and load the dump files into your database.
If you followed the instructions for setting up MySQL in the Leginon Install guide, you have already created dbemdata and projectdata databases.
If you don't have them, create them first.

    mysql -u root projectdata < ProjectLogin.sql

## 3 Modify Config.php

This is the Myami config file. It is being changed right now so this is in flux. Will update soon.

It should look like this:

    // --- Set your leginon MySQL database server parameters

    $DB_HOST        = "localhost";
    $DB_USER        = "usr_object";
    $DB_PASS        = "";
    $DB             = "dbemdata";

    // --- XML test dataset
    $XML_DATA = "test/viewerdata.xml";

    // --- Project database URL

    $PROJECT_URL = "project";
    $PROJECT_DB_HOST = "localhost";
    $PROJECT_DB_USER = "usr_object";
    $PROJECT_DB_PASS = "";
    $PROJECT_DB = "projectdata";

## 4 Populate your databases automagically

Point your web browser to http://localhost/myamiweb/.
Navigate to the Administration page and then to the ProjectDB page.

Doing this will populate your database with the schema defined in myami/myamiweb/project/defaultprojecttables.xml.
If you need to repopulate tables, use phpMyadmin to empty the Install table in the project DB. Then repeat the steps above.
