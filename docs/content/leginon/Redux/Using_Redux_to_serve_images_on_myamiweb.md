These instructions cover installation of Leginon and Appion web tools for viewing images and performing image processing through the web server using Redux as an image server.
Redux is new for CentOS 6 (PHP 5.3).

## Installation

-   Install python filesystem abstraction for redux caching:
        sudo easy_install fs==0.5
-   Install Myami packages
        cd myami
        ./pysetup.sh install

## Copy the myami/myamiweb directory to your Apache web directory

Example:

    cd myami

    #CentOS example
    sudo cp -vr myamiweb /var/www/html/ 

    #this is temporary for setup, revert to 755 when finished with this page
    sudo chmod 777 /var/www/html/myamiweb  

    #if you have SELinux enabled this command will help
    sudo chcon -R --type=httpd_sys_content_t /var/www/html

## Configuration Redux

    > cd /YourMyamDownload/redux
    > cp redux.cfg.template redux.cfg

-   You can also copy it to /etc/myami/redux.cfg if you prefer.
-   Set a writable log path by the user starting it. In this example, we start redux as root and save the log in /var/log/redux.log
-   Edit the redux.cfg file as follows:
     
        [log]
        file: /var/log/redux.log

    
     
-   Turn on redux caching if desired:
     
        [cache]
        enable: yes
        path: /var/cache/myami/redux
        disksize:  500
        memsize: 500

    
     
    -   **You need to make sure the cache path exists and writable by the user that starts the redux server (reduxd)**
    -   Input the desired disk_cache_path, disk_cache_size, and mem_cache_size in the next few lines
    -   Create the disk_cache_path before running redux if cache will be used

## Configure Web Interface (myamiweb)

There is a setup wizard available to help you set the configuration parameters for your installation. If you prefer not to use the wizard, there are instructions for manually editing the configuration file. If this is your first time creating the web tool configuration file, we recommend using the setup wizard.

### Configuration using the setup wizard

The setup wizard will check your database connection, create required database tables, and perform default data initialization.

* Run the online setup wizard by visiting http://yourhost/myamiweb/setup or http://localhost/myamiweb/setup to create the myami website's config file.
 
**Tips:**

1.  You need to know your database setup before you start. If you have been using the parameters in this instruction, here is a [summary](/leginon/Leginon_Manual/Complete_Installation/Processing_Server_Installation/Explanation_of_Sample_Names).
2.  To discover what the Apache user is:
        sudo egrep -iw --color=auto '^(user|group)' /etc/httpd/conf/httpd.conf
3.  You also need to decide whether you would like to enable the [user management system](/leginon/appionWhat_does_User_Authentication_do_to_myamiweb).

[Manual configuration instructions (Advanced User)]{.underline}

Go to [appion:Install the Web Interface Advanced](/leginon/appionInstall_the_Web_Interface_Advanced) for the advanced configuration.

### Revert permissions

    sudo chmod 755 /var/www/html/myamiweb

## Test Redux Installation

# Using Redux to do simple input output (simple client with no reduxd server needed):

    redux --filename=test.jpg --oformat=PNG > test.png

Make sure the resulting test.png is in fact an image and not an error message.

# Run the server: run the following on a command line:

    reduxd

leave it running for the following...

# Test command line client connecting to the server

    redux --server_host=localhost --filename=/absolute_path/test.jpg --oformat=PNG > test.png

Note: **The input file name is from the perspective of the reduxd server**, so be sure to give it an absolute path (unlike the first test, which was not accessing the server)

1.  Check the redux.log created as configured in redux.cfg. This contains the port opened by redux server that will allow myamiweb to connect to.

## Setup fftw to use wisdom

**This applies only if you see the messge "* Using custom copy of fftw3"** in the previous redux test.

fftw runs much faster on odd image dimension if a wisdom is saved. It is best to create the wisdom ahead of time using the stand alone script pyami/fft/fftwsetup.py. It will store the wisdom you create in your home directory with a name like 'fftw3-wisdom-hostname'. If you only start reduxd as root and fftwsetup.py is run as root, this is enough.

-   Redux needs write permission at its installation location to write fftw wisdom file.
-   For developer only: you can copy the wisdom file to any other home directory that wants to use it, or copy it as root to a file called /etc/fftw/wisdom which any user can access.

### Using fftwsetup.py:

FIrst, you need to know the typical image dimension redux needs to process, especially the large ones and **ones that are not powers of 2 such as those produced by Gatan K2**.

    cd /YourMyamDownload/pyami/fft
    ./fftwsetup.py 1 number_of_rows number_of_colums

For example, for K2 summit super-resolution image there are 7676 rows and 7420 columns, therefore, the command line is

    ./fftwsetup.py 1 7676 7420


This may take a few minutes.

Run this for as many dimensions you know will be used and move it for general use as instructed above if preferred.

## Start the Redux server for use with myamiweb

Start reduxd server if not already running from the above test:

    reduxd

## Starting reduxd at boot

**CentOS6 and CentOS7**

    sudo cp -v myami/redux/init.d/reduxd /etc/init.d/
    sudo service reduxd start

**Using systemd on CentOS7 or Ubuntu**

Please follow [this instruction](/leginon/Redux/Using_Redux_to_serve_images_on_myamiweb/Start_redux_with_systemd) provided by Partick Goetz

## Test the myamiweb and Redux installation

1.  Visit http://yourhost/myamiweb or http://localhost/myamiweb to confirm functionality of the myamiweb website.
2.  Browse to the automatic web server troubleshooter at: http://localhost/myamiweb/test/checkwebserver.php
3.  Click on "[test dataset]" on your main myamiweb home page, or go directly to the URL: myamiweb/viewerxml.php
4.  Test by accessing your own images from Leginon in myamiweb/imageviewer.php

## Turn off error checking in php.ini

Once functionality is confirmed, you may turn off the display of website errors.
Edit the following items in php.ini (found as /etc/php.ini on CentOS and /etc/php5/apache2/php.ini on SuSE) so that they look like the following:

> display_errors = Off

## Troubleshooting image display

If you find that you have many users viewing images, and the images are taking too long to load, there are several ways to address this.

1.  [leginon:Alternative reduxd installation on file server](/leginon/leginonAlternative_reduxd_installation_on_file_server)
2.  [leginon:Using imcache to cache mrc images as jpeg images of the default size on myamiweb](/leginon/leginonUsing_imcache_to_cache_mrc_images_as_jpeg_images_of_the_default_size_on_myamiweb)
