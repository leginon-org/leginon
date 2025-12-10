Create the following info.php in your web server document root directory (/var/www/html on CentOS. /srv/www/htdocs on SuSE. You can find its location in httpd.conf mentioned above under the line starting DocumentRoot).

    sudo nano /var/www/html/info.php

Copy and paste the following code into info.php:

    <?php
    phpinfo();
    ?>

Restrict access to your info.php file.

    sudo chmod 444 /var/www/html/info.php

Visit this page at http://HOST.INSTITUTE.EDU/info.php or http://localhost/info.php

You will see comprehensive tables of php and apache information, including the location of the additional .ini files, extension, include path, and what extension is enabled.

Here is an example screen shot of the part of the info.php page that tells you where php.ini and other configuration files are. This information will be used while installing components of the Web Server.

![](images/phpini.png)

[< Start NFS](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation/Start_NFS) | [Install SSH module for PHP >](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation/Install_SSH_module_for_PHP_webserver)
