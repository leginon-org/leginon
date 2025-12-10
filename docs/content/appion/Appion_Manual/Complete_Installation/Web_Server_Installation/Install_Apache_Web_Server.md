1. Install the Apache Web Server with the YaST or yum utility.

2. Find "httpd.conf".
This is /etc/httpd/conf/httpd.conf on CentOS and /etc/apache2/httpd.conf on SuSE

    sudo nano /etc/httpd/conf/httpd.conf

3. Edit the "httpd.conf" configuration file with the following:


DirectoryIndex index.html index.html.var index.php

HostnameLookups On


**Note:** It may be possible to edit httpd.conf in YaST2 as well.

4. If you plan to enable the web interface user login feature, the ServerName directive should be set to a resolvable host name and UseCanonicalnames should be turned on. This will ensure the link provided in the email to verify user registration is valid. Follow the example below replacing YourServer.yourdomain.edu with your servers name.


ServerName YourSever.yourdomain.edu

UseCanonicalName On


5. Restart the web server.

    apachectl restart
         or
    sudo /sbin/service httpd restart     (ON CentOS/RHEL/Fedora)
         or
    /etc/sbin/rcapache2 restart   (ON SuSE)
         or
    /sbin/service httpd restart

If you want to start the web server automatically at boot on SuSE

    sudo /sbin/chkconfig apache2 on  #SuSE
    sudo /sbin/chkconfig httpd on  #CentOS/RHEL/Fedora

See also: [How to start Apache at Startup on Centos or Red Hat Enterprise Linux using chkconfig](http://thevagabondgeek.com/12-how-to-start-apache-at-startup-on-centos-or-red-hat-enterprise-linux-using-chkconfig).

[< Configure php.ini](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation/Configure_phpini) | [Start NFS >](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation/Start_NFS)
