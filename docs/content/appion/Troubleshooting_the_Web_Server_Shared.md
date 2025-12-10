#### Run the web server troubleshooter

A web server troubleshooting tool is available at http://YOUR_HOST/myamiweb/test/checkwebserver.php.
You can browse to this page from the Appion and Leginon Tools home page (http://YOUR_HOST/myamiweb) by clicking on [test Dataset] and then [Troubleshoot].

This page will automatically confirm that your configuration file and PHP installation and settings are correct and point you to the appropriate documentation to correct any issues.

#### Firewall settings

You may need to configure your firewall to allow incoming HTTP (port 80) and MySQL (port 3306) traffic:

    $ system-config-securitylevel

#### Security-enhanced linux

[Security-enhanced linux (SELinux)](http://en.wikipedia.org/wiki/Security-Enhanced_Linux) may be preventing your files from loading. To fix this run the following command:

    $ sudo /usr/bin/chcon -R -t httpd_sys_content_t /var/www/html/

see [this website](http://docs.fedoraproject.org/selinux-apache-fc3/sn-simple-setup.html) for more details on SELinux

#### Slow image loading

If you find that you have many users viewing images, and the images are taking too long to load, there are several ways to address this.

1.  [leginon:Alternative reduxd installation on file server](/appion/leginonAlternative_reduxd_installation_on_file_server)
2.  [leginon:Using imcache to cache mrc images as jpeg images of the default size on myamiweb](/appion/leginonUsing_imcache_to_cache_mrc_images_as_jpeg_images_of_the_default_size_on_myamiweb)

#### Seg fault errors messages in Apache log: Web server does not inform user when login credentials are incorrect

If you try to run a job directly from the web gui, and the job fails without providing a message, check to see if it could be due to bad credentials. Test a username or password that you know are incorrect. If you do not receive a clear error message in the GUI, try the following fix.

Install latest version of http://pecl.php.net/package/ssh2:

    wget http://pecl.php.net/get/ssh2-0.12.tgz
    tar -xzvf ssh2-0.12.tgz 
    cd ssh2-0.12
    yum install automake make php-devel libtool openssl-devel gcc++ gcc
    phpize
    yum install gcc php-devel php-pear libssh2 libssh2-devel
    ./configure 
    make
    make test
    cp modules/ssh2.so   /usr/lib64/php/modules/
    service httpd restart

There were `Segmentation fault` messages in the apache error log and I narrowed it down to [Cluster->authenticatedConnection()](https://emg.nysbc.org/redmine/projects/appion/repository/entry/trunk/myamiweb/processing/inc/cluster.inc#L293)

It seems that the fix for [PHP :: Bug #63192](https://bugs.php.net/bug.php?id=63192) was needed to fix this bug.
