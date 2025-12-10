import the sql files of your mysqldump into the empty database ("usr_object" need to have privilages to create table):

    mysql -h database_host -u usr_object -p leginondb < leginondb.sql
    mysql -h database_host -u usr_object -p projectdb < projectdb.sql

_

[< Save a copy of the databases](/leginon/Leginon_Manual/Trouble_shooting/Mysqldump_of_your_database)
