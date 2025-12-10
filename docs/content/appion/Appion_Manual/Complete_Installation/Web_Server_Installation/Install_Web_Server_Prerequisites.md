The myamiweb files are mostly php scripts that run at the web server. PHP, PHP-devel, gd, and fftw3 packages are required before installation of myamiweb and the mrc extension that handles the display of mrc files. Some of these packages may be found on the SuSE Linux DVD or included in common package repository. MySQL and the Apache Web Server can be downloaded from their respective websites.

### Extra Packages for Enterprise Linux (EPEL)


- http://fedoraproject.org/wiki/EPEL
- contains a wealth of packages required for appion

Download repository rpm and install

wget 'http://mirrors.cat.pdx.edu/epel/6/i386/epel-release-6-8.noarch.rpm'
sudo yum ---nogpgcheck localinstall epel-release-6-8.noarch.rpm

Note that release version (6-8) is the current release at the time of this writing. Please visit http://fedoraproject.org/wiki/EPEL/FAQ#How_can_I_install_the_packages_from_the_EPEL_software_repository.3F for more up-to-date information on how to install the packages from the EPEL software repository.


### Install Supporting Packages

-   Use the installation tools available for your linux distribution.
    For example, to install gd as php extension you may use
        CentOS> sudo yum install php-gd
        SuSE10.2 and above> zypper install php-gd

    
    Likewise, use the SuSE Linux YaST2 utility or zypper (openSuSE 10.2 and above) to install.
    [An older list of required CENTOS rpms and instruction](http://emg.nysbc.org/redmine/boards/10/topics/685) can be found in the Forum.


-   Use the following table to find and install the prerequisite packages required for your distribution of linux:

**Prerequisite packages for myamiweb:**

The following table lists the packages required for running the web server on CentOS 5 for Appion/Leginon 2.2 and earlier.

  Name:                                                           Download site:                                                                                                        yum package name                     SuSE rpm name
  --------------------------------------------------------------- --------------------------------------------------------------------------------------------------------------------- ------------------------------------ ---------------
  Apache                                                          [www.apache.org](http://www.apache.org)                                                                               httpd                                apache2
  php                                                             [www.php.net](http://www.php.net)                                                                                     php                                  php
  php-devel*                                                     [rpmfind.net/linux/RPM/Development_Languages_PHP.html](http://rpmfind.net/linux/RPM/Development_Languages_PHP.html)   php-devel                            php-devel
  php-mysql*                                                     [rpmfind.net/linux/RPM/Development_Languages_PHP.html](http://rpmfind.net/linux/RPM/Development_Languages_PHP.html)   php-mysql                            php-mysql
  php-gd                                                          [www.php.ned/gd](http://www.libgd.org) (Use gd2)                                                                      php-gd                               php-gd
  fftw3 library (including development libraries and header *)   [www.fftw.org](http://www.fftw.org) (Use fftw3.x)                                                                     fftw3-devel                          fftw3-devel
  libssh2 devel                                                   http://www.libssh2.org                                                                                                libssh2-devel (found in epel repo)   libssh2-devel
  phpMyAdmin (optional)                                           http://www.phpmyadmin.net                                                                                             phpMyAdmin                           
  GCC, the GNU Compiler Collection                                http://gcc.gnu.org                                                                                                    gcc                                  
  Apache SSL module                                                                                                                                                                     mod_ssl                              
  SSH PECL extension                                              http://www.php.net/manual/en/ssh2.installation.php                                                                    php-pecl-ssh2                        php-pecl-ssh2
                                                                                                                                                                                        svn                                  
                                                                                                                                                                                        git                                  
                                                                                                                                                                                        python-imaging                       
                                                                                                                                                                                        python-devel                         
                                                                                                                                                                                        mod_python                           
  SciPy 0.5.1 (tested, others may work)*                         <http://www.scipy.org>                                                                                                scipy                                python-scipy
                                                                                                                                                                                        fs 0.5                               
                                                                                                                                                                                        PyFFTW3                              

You can install all of these on CentOS with the following commands:

    #CentOS> 
    yum install php-pecl-ssh2 mod_ssl fftw3-devel git python-imaging python-devel mod_python scipy httpd libssh2-devel php php-mysq phpMyAdmin.noarch php-devel php-gd'

    easy_install fs==0.5 PyFFTW3

**Notes:**

-   RPM.pbone.net http://rpm.pbone.net/ provides a nice interface to search for module names on RPM based systems.
-   GD is usually installed with php. If you find that you can only view images as png instead of jpg, it may be that you do not have gd *jpeg* support installed.

[< Differences between Linux flavors](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation/Differences_between_Linux_flavors) | [Configure php.ini >](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation/Configure_phpini)
