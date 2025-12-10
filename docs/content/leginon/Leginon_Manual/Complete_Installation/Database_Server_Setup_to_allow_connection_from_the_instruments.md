## Allow remote access to database server (default in CentOS 6 and CentOS 7).

### Edit /etc/my.cnf search for **skip-networking** and make sure it is commented out like this:

    #skip-networking

Also look for bind-address in the same file and if it says 127.0.0.1, it will only listen to local connection.
You should comment that out as well.

    #bind-address=127.0.0.1

### Restart mysqld if you have made changes.

For CentOS7 that runs mariadb,

    sudo systemctl restart mariadb

For CentOS6, Fedora that runs mysql

    sudo /etc/init.d/mysqld restart


or

    sudo /sbin/service mysqld restart

## Create remote user if autoinstaller was used

Autoinstaller creates only root user and only allow its access to database from the localhost.

The following assumes that you want to use usr_object user for remote access as referenced in most of this document.

### Create and grant privileges to the usr_object for the databases on the hosts involved. See MySQL Reference Manual for details.

You can set hosts on a particular subnet by only specify the network number portion such as '192.168' and use wild card for the host number portion to give '192.168..' as the global host allowing connection.
If appropriate, you can also use domain name with wild card, i.e., '%.mydomain.edu'

Start mysql command line interface in a terminal as root and access the database named mysql which manages users and permission. We assume that you have used autoinstaller here and hence the password for root using in mysql is not yet set.

For CentOS7 running mariadb

    mysql -u root -p mysql


The mysql root user password is set during autoinstallation and is the same as your host root password you gave.

For CentOS6 running mysql

    mysql mysql

At the mysql prompt execute the following commands:

    CREATE USER usr_object@'192.168.%.%' IDENTIFIED BY 'YOUR_PASSWORD';
    GRANT ALTER, CREATE, INSERT, SELECT, UPDATE ON leginondb.* TO usr_object@'192.168.%.%';
    GRANT ALTER, CREATE, INSERT, SELECT, UPDATE ON projectdb.* TO usr_object@'192.168.%.%';

    CREATE USER usr_object@'localhost' IDENTIFIED BY 'YOUR_PASSWORD';
    GRANT ALTER, CREATE, INSERT, SELECT, UPDATE ON leginondb.* TO usr_object@'localhost';
    GRANT ALTER, CREATE, INSERT, SELECT, UPDATE ON projectdb.* TO usr_object@'localhost';

    flush privileges;
    exit;

### Other changes if usr_object will be used all the time from now on in autoinstalled Leginon:

**webserver** myamiweb/config.php

    define('DB_USER', 'usr_object');
    define('DB_USER','YOUR_PASSWORD');

**processing server** /etc/myami/sinedon.cfg or ,if it does not exist, see [Configure sinedoncfg](/leginon/Leginon_Manual/Complete_Installation/Processing_Server_Installation/Configure_sinedoncfg) for other possibilities

    user: usr_object
    passwd: YOUR_PASSWORD

[< Web Server Installation](/leginon/Leginon_Manual/Complete_Installation/Web_Server_Installation) | [Additional Database Server Setup >](/leginon/Leginon_Manual/Complete_Installation/Additional_Database_Server_Setup_after_Web_Server_Installation)
