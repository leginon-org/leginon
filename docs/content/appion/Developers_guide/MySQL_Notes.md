## restart mysql on centOS

     /etc/init.d/mysqld restart 

## Find out which installation is being used

    which mysql

## Get access to our databases

To get access to our databases, you need to ask Christopher (or someone else with the correct privileges) to add you as a user.
Our databases reside on Cronus4 (Appion and Leginon things), ami (websites and tools like Redmine), and Fly (a copy of Cronus4 used for testing).
Once added, you will need to change your password from the default to something all your own on each server that you are added to. Here's how:

At a terminal type:

    mysql -h cronus4 -u [yourUserName] -p

You are prompted to type your default password. Then, change your password with:

    set password = password("[new password]");

## Other MySQL commands to try

show databases;
use [name of db]
show tables;
describe [name of table];

## To stop a query that is taking too long:

    mysql> showprocesslist;

    mysql> kill [process Id number];

## Mysql bug with nested subqueries

[Mysql Nested Subqueries Problem](/appion/Developers_guide/MySQL_Notes/Mysql_Nested_Subqueries_Problem)
