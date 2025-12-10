Different Linux flavors often put web server and mysql-related files in different locations. This can be confusing. From experience, we found the equivalent on CentOS vs SuSE. Here we list them for reference. If your system uses different naming and you are willing to share your experience, please send us the list. We will add it here:

Table Different File locations and Commands on CentOS vs SUSE

  File or Command Head                     CentOS                 SuSE
  ---------------------------------------- ---------------------- ---------------------
  php.ini                                  /etc/                  /etc/php5/apache2/
  httpd.conf                               /etc/httpd/conf/       /etc/php5/apache2/
  default document_root                    /var/www/html/         /srv/www/htdocs/
  apache start/stop/restart command head   /sbin/service httpd    /etc/init.d/apache2
  mysql start/stop/restart command head    /sbin/service mysqld   /etc/init.d/mysql

For a more detailed comparison of Apache file layout on different Linux distributions, see http://wiki.apache.org/httpd/DistrosDefaultLayout

[< Configure Operating System](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation/Configure_Operating_System) | [Install Web Server Prerequisites >](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation/Install_Web_Server_Prerequisites)
