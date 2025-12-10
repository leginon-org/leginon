## Install MySQL

The following is for the computer that hosts the databases. This involves installing MySQL server and creation/configuration of the leginondb and projectdb databases.

### 1 Install MySQL-Server and MySQL-Client

**Note:** You may already have MySQL Server and Client installed. Check by typing mysql at the command line.
If you see a MySQL prompt (mysql>), you may skip this step.

To install Mysql on Linux you have two options (the first option is better):

# Use your package installer (yum, zypper, YaST, apt-get). For example:


sudo yum install mysql mysql-server


For Suse


yast2 -i mysql mysql-client


1.  Download the latest MySQL-server package for Linux from http://www.mysql.com

### 2 Locate Example MySQL configuration files

They are usually located in /usr/share/mysql.

    ls /usr/share/mysql/my*
        /usr/share/mysql/my-huge.cnf
        /usr/share/mysql/my-innodb-heavy-4G.cnf
        /usr/share/mysql/my-large.cnf
        /usr/share/mysql/my-medium.cnf
        /usr/share/mysql/my-small.cnf


If that does not work try the locate function

    locate my | egrep ".cnf$"
        /etc/my.cnf
        /usr/share/mysql/my-huge.cnf
        /usr/share/mysql/my-innodb-heavy-4G.cnf
        /usr/share/mysql/my-large.cnf
        /usr/share/mysql/my-medium.cnf
        /usr/share/mysql/my-small.cnf

### 3 Configure my.cnf in /etc using my-huge.cnf as the template

1.  Copy my-huge.cnf to my.cnf
        sudo cp -v /usr/share/mysql/my-huge.cnf /etc/my.cnf
2.  Edit /etc/my.cnf to add or change query cache variables like these (be sure to place them under the `[mysqld]` section):
        query_cache_type = 1
        query_cache_size = 100M
        query_cache_limit= 100M
3.  Search for the text default_storage_engine in /etc/my.cnf. **VERY IMPORTANT** **If it exists and is set to other than MyISAM, you should change it** to:
        default_storage_engine=MyISAM

### 4 Start the MySQL Server

Most modern linux systems use systemd:

    sudo systemctl start mysql

or

    sudo systemctl start mysqld

For CentOS/Fedora/RHEL v. 6.x systems use the service command:

    sudo /sbin/service mysqld start

For older Unix systems:

    sudo /etc/init.d/mysqld start

or on some installations (Suse),

    sudo /etc/init.d/mysql start

For future reference: start | stop | restart MySQL Server with similar commands:

For Centos, Fedora

    sudo /etc/init.d/mysqld start
    sudo /etc/init.d/mysqld stop
    sudo /etc/init.d/mysqld restart


or

    sudo /sbin/service mysqld start
    sudo /sbin/service mysqld stop
    sudo /sbin/service mysqld restart


or for Suse

    sudo /etc/init.d/mysql start
    sudo /etc/init.d/mysql stop
    sudo /etc/init.d/mysql restart

### 5 Configure MySQL to start automatically at boot

    sudo systemctl enable mysql

or

    sudo systemctl enable mysqld

depending on what the systemd service file is called for your system.

For CentOS v. 6.x systems:

    sudo /sbin/chkconfig mysqld on

or for older SuSe systems:

    sudo /sbin/chkconfig --add mysql

### 6 For future reference, the database location will be:

    ls /var/lib/mysql
        ibdata1  ib_logfile0  ib_logfile1  mysql  mysql.sock  test

### 7 Create the Leginon database, call it leginondb

    sudo mysqladmin create leginondb

### 8 Create the Project database, call it projectdb

    sudo mysqladmin create projectdb

### 9 Connect to mysql db

If starting from scratch, the mysql root user will have no password. This is assumed to be the case and we will set it later.

    mysql -u root mysql

You should see a mysql prompt: mysql>

You can view the current mysql users with the following command.

    select user, password, host from user;
          +------+----------+-----------+
          | user | password | host      |
          +------+----------+-----------+
          | root |          | localhost |
          | root |          | host1     |
          |      |          | host1     |
          |      |          | localhost |
          +------+----------+-----------+
          4 rows in set (0.00 sec)

### 10 Create user

Create and grant privileges to a user called usr_object for the databases on both the localhost and other hosts involved. For example, use wild card '%' for all hosts. You can set specific (`ALTER, CREATE, DROP, DELETE, INSERT, RENAME, SELECT, UPDATE`) privileges or `ALL` privileges to the user. See MySQL Reference Manual for details. The following examples demonstrate some of the options available.

-   **Option 1: More secure - restrict Drop and Delete privileges**
     
    At the mysql prompt execute the following commands:
        CREATE USER usr_object@'localhost' IDENTIFIED BY 'YOUR PASSWORD';
        GRANT ALTER, CREATE, INSERT, SELECT, UPDATE ON leginondb.* TO 'usr_object'@'localhost';
        GRANT ALTER, CREATE, INSERT, SELECT, UPDATE ON projectdb.* TO 'usr_object'@'localhost';

Note: For MySQL version 8 use the following command instead to create a user:

    CREATE USER usr_object@'localhost' IDENTIFIED WITH mysql_native_password BY 'YOUR PASSWORD';


Thanks to - https://stackoverflow.com/questions/49963383/authentication-plugin-caching-sha2-password

-   **Option 2: Less secure - allow all privileges**
     
    You may choose to use the following less secure version (no password and all privileges) of the commands above, however, we recommend not allowing the DROP privilege on all tables nor DELETE privilege on most tables.
     
    At the mysql prompt execute the following commands:
        CREATE USER usr_object@'localhost';
        GRANT ALL PRIVILEGES ON leginondb.* TO 'usr_object'@'localhost';
        GRANT ALL PRIVILEGES ON projectdb.* TO 'usr_object'@'localhost';


-   **Option 3: Allow access from all computers in the domain**
     
    You may also choose to assign a domain to your commands and use a wildcard to allow access from all computers in the domain.
     
        CREATE USER usr_object@'%.mydomain.edu' IDENTIFIED BY 'YOUR PASSWORD';
        GRANT ALTER, CREATE, INSERT, SELECT, UPDATE ON leginondb.* to 'usr_object'@'%.mydomain.edu';
        GRANT ALTER, CREATE, INSERT, SELECT, UPDATE ON projectdb.* to 'usr_object'@'%.mydomain.edu';

### 11 Give create and access privileges for the processing databases which begin with "ap".

    # if your web host is local
    GRANT ALTER, CREATE, INSERT, SELECT, UPDATE, DELETE ON `ap%`.* to 'usr_object'@localhost; 
    # for all other hosts if you are accessing the databases from another computer
    GRANT ALTER, CREATE, INSERT, SELECT, UPDATE, DELETE ON `ap%`.* to 'usr_object'@'%.mydomain.edu';       

### 12 Change Root password

To set the root password use the command:

    sudo mysqladmin -u root password NEWPASSWORD

Or you can do it from within mysql

    update user set password=password('your_own_root_password') where user="root";
    Query OK, 2 rows affected (0.01 sec)
    Rows matched: 2  Changed: 2  Warnings: 0

    # run the flush privileges command to avoid problems
    flush privileges;
    ^D or exit;

From now on, you will need to specify the password to connect to the database as root user like this:

    mysql -u root -p mysql

### 13 Check MySQL variables

    # at the command prompt, log into the leginon database

    mysql -u usr_object -p leginondb

    # At the mysql prompt show variables that begin with 'query'.
    # Check that the changes you made to my.cfg are in place.

    SHOW VARIABLES LIKE 'query%';
          +------------------------------+-----------+
          | Variable_name                | Value     |
          +------------------------------+-----------+
          | ft_query_expansion_limit     | 20        |
          | have_query_cache             | YES       |
          | long_query_time              | 10        |
          | query_alloc_block_size       | 8192      |
          | query_cache_limit            | 104857600 | ---This should correspond to your change
          | query_cache_min_res_unit     | 4096      |
          | query_cache_size             | 104857600 | ---This should correspond to your change
          | query_cache_type             | ON        | ---This should correspond to your change
          | query_cache_wlock_invalidate | OFF       |
          | query_prealloc_size          | 8192      |
          +------------------------------+-----------+
          10 rows in set (0.00 sec)

    exit;

If you do not see your changes, try restarting mysql.
On centOS:

    sudo /etc/init.d/mysqld restart

### 14 Make sure MySQL is running

    mysqlshow -u root -p
          +--------------+
          | Databases    |
          +--------------+
          | mysql        |
          | leginondb    |
          | projectdb    |
          +--------------+

### Run the following command from the command line:

Be sure to edit PASSWORD to the one you previously set for usr_object.

    php -r "mysql_connect('localhost', 'usr_object', 'PASSWORD', 'leginondb'); echo mysql_stat();"; echo ""

Expected output:

    Uptime: 1452562 Threads: 1 Questions: 618 Slow queries: 0 Opens: 117 Flush tables: 1 Open tables: 106 Queries per second avg: 0.000

If there are any error messages, mysql may be configured incorrectly.

**Note:** If you do not have php and php-mysql packages installed you need to install them to run the above command. The yum installation is:

    sudo yum -y install php php-mysql


