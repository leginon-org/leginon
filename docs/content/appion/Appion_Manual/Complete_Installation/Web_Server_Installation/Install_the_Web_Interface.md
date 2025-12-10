Install Leginon and Appion web tools for viewing images and performing image processing through the web server.

## 1. Install pyami

The web interface will at least need the myami/pyami package to do MRC to JPEG conversion. Install myami/pyami as follows:

    cd myami/pyami
    sudo python setup.py install


This will install the script "mrc2any" into /usr/bin/mrc2any (for typical linux system). You can customize the location with options to the setup.py command.
To be sure where it was installed, run:

    which mrc2any

You will need to know that location when configuring below.

## 2. Copy the myami/myamiweb directory to your Apache web directory

Example:

    cd myami

    #CentOS example
    sudo cp -vr myamiweb /var/www/html/ 

    #this is temporary for setup, revert to 755 when finished with this page
    sudo chmod 777 /var/www/html/myamiweb  

    #if you have SELinux enabled this command will help
    sudo chcon -R --type=httpd_sys_content_t /var/www/html

## 3. Configure your installation

There is a setup wizard available to help you set the configuration parameters for your installation. If you prefer not to use the wizard, there are instructions for manually editing the configuration file. If this is your first time creating the web tool configuration file, we recommend using the setup wizard.

### Configuration using the setup wizard

The setup wizard will check your database connection, create required database tables, and perform default data initialization.

* Run the online setup wizard by visiting http://yourhost/myamiweb/setup or http://localhost/myamiweb/setup to create the myami website's config file.
 
**Tips:**

1.  You need to know your database setup before you start. If you have been using the parameters in this instruction, here is a [summary](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Explanation_of_Sample_Names).
2.  To discover what the Apache user is:
        sudo egrep -iw --color=auto '^(user|group)' /etc/httpd/conf/httpd.conf
3.  You also need to decide whether you would like to enable the [user management system](/appion/appionWhat_does_User_Authentication_do_to_myamiweb).

### Manual configuration instructions (Advanced User)

Go to [Install the Web Interface Advanced](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation/Install_the_Web_Interface/Install_the_Web_Interface_Advanced) for the advanced configuration.

## 4. Revert permissions

    sudo chmod 755 /var/www/html/myamiweb

## 5. Test the installation

Visit http://yourhost/myamiweb or http://localhost/myamiweb to confirm functionality.
You may also browse to the automatic web server troubleshooter at: http://localhost/myamiweb/test/checkwebserver.php

## 6. Turn off error checking in php.ini

Edit the following items in php.ini (found as /etc/php.ini on CentOS and /etc/php5/apache2/php.ini on SuSE) so that they look like the following:

> display_errors = Off

[< Install SSH module for PHP](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation/Install_SSH_module_for_PHP_webserver) | [Install phpMyAdmin >](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation/Install_phpMyAdmin)
