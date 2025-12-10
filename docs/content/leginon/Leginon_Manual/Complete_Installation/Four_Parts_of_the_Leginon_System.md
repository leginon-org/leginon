![](images/Leg_Proj_parts.png)

Leginon as a system that we distribute can be divided into three parts:

## Processing Server (Python-side)

Python (and some c) scripts that handle instrument control, data acquisition, and
processing.

## Database Server (MySQL-side)

a MySQL server that handles the database

## Web Server (PHP-side)

This includes php and Java scripts at a webserver that we will create to retrieve image
and metadata from the database and file-storage system.

## File Server

This is up to you to set up to store lots of data coming out of Leginon system.

[What is in this Chapter >](/leginon/Leginon_Manual/Complete_Installation/What_is_in_this_Chapter)
