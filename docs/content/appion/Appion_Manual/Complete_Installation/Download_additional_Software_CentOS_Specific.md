## Install the additional package repositories

There are several additional CentOS repositories that you can install. These repositories provide additional packages, such as patented software (MP3 players), closed source applications (Flash plugin, Adobe Acrobat Reader) and lesser used packages (python numpy, Gnu Scientific Library). But some repositories install packages over other packages, which can cause problems and conflicts (ATrpms is bad at this). So we recommend only installing EPEL and RPM Fusion. Read more here:
[CentOS Additional Repositories](http://wiki.centos.org/AdditionalResources/Repositories)
Particularly, pay attention to the note about protecting yourself from unintended updates from 3rd party packages. The following yum plugin may help you:
[yum-priorities plugin](http://wiki.centos.org/PackageManagement/Yum/Priorities)

### Extra Packages for Enterprise Linux (EPEL)


- http://fedoraproject.org/wiki/EPEL
- contains a wealth of packages required for appion

Download repository rpm and install

wget 'http://mirrors.cat.pdx.edu/epel/6/i386/epel-release-6-8.noarch.rpm'
sudo yum ---nogpgcheck localinstall epel-release-6-8.noarch.rpm

Note that release version (6-8) is the current release at the time of this writing. Please visit http://fedoraproject.org/wiki/EPEL/FAQ#How_can_I_install_the_packages_from_the_EPEL_software_repository.3F for more up-to-date information on how to install the packages from the EPEL software repository.


### RPM Fusion (optional)

-   http://rpmfusion.org/
-   good for mp3 and other patent limited software

Download repository rpms and install

    sudo rpm -Uhv http://download1.rpmfusion.org/free/el/updates/testing/5/`uname -i`/rpmfusion-free-release-5-0.1.noarch.rpm
    sudo rpm -Uvh http://download1.rpmfusion.org/nonfree/el/updates/testing/5/`uname -i`/rpmfusion-nonfree-release-5-0.1.noarch.rpm

## Update current packages

Update the updater to make life easier

    sudo yum -y update yum*

### Update all packages

    sudo yum -y update

**NOTE**

> Download was over 129 MB (in July 2009) and 333 MB (in May 2010). If you have a slow internet connection you can setup presto/deltarpms, see [this email](http://www.linux-archive.org/centos-development/222706-presto-deltarpm.html) and [this email](http://www.centos.org/modules/newbb/viewtopic.php?topic_id=8349) for more information

**NOTE**

> Sometimes I have problems with 32bit packages, so uninstall of them:

    rpm -qa --qf "%{NAME}.%{ARCH}\n" | grep i.86 | wc -l
    sudo yum remove `rpm -qa --qf "%{NAME}.%{ARCH}\n" | grep i.86`

**NOTE**

> You can also remove large packages like openoffice, java, and gimp to save space, if you are just making a server

    sudo yum remove openoffice* gimp* java*

You will want to restart your computer when this completes.

    sudo reboot

### Install Complete list of additional packages:

General instructions for installation and configuration of some of these packages (such as mysql) are found later in this manual. It may be faster to install them now as a group rather than individually, but it is not necessary.

-   **python tools**: python-tools python-devel
-   **general applications**: subversion ImageMagick grace gnuplot python-matplotlib pstopnm (netpbm-progs)
-   **Tilt Picker**: wxPython numpy scipy python-imaging
-   **FindEM**: gcc-gfortran compat-gcc-34-g77
-   **Ace 2**: gcc-objc fftw3-devel gsl-devel
-   **Sinedon**: mysql mysql-server MySQL-python
-   **Myamiweb**: httpd php php-mysql phpMyAdmin
-   **Xmipp MPI**: gcc-c openmpi-devel libtiff-devel
-   **UCSF Chimera imaging**: xorg-x11-server-Xvfb
-   **PHP-SSH2**: libssh2-devel

If you are using an RPM based system (e.g., SuSE, Mandriva, CentOS, or Fedora) [this website](http://rpm.pbone.net/) is good for determining the exact package name that you need. For CentOS 5, just type:

    sudo yum -y install 
    python-tools python-devel python-matplotlib 
    subversion ImageMagick grace gnuplot 
    wxPython numpy scipy python-imaging 
    gcc-gfortran compat-gcc-34-g77 
    gcc-objc fftw3-devel gsl-devel 
    mysql mysql-server MySQL-python 
    httpd php php-mysql phpMyAdmin  
    gcc-c++ openmpi-devel libtiff-devel 
    php-devel gd-devel re2c fftw3-devel php-gd 
    xorg-x11-server-Xvfb netpbm-progs 
    libssh2-devel

If you have an nVidia video card and setup RPM fusion, install the nVidia binary, will speed things up especially for UCSF Chimera. This command works on Fedora

    sudo yum -y install nvidia-x11-drv

for CentOS you will have to download and install the nvidia driver from the [nvidia website](http://www.nvidia.com)

#### Clean up packages to save drive space

    sudo yum clean all

#### Re-index the hard drive, this will come in handy later

    sudo updatedb

#### Enable web and database servers on reboot

    sudo /sbin/chkconfig httpd on
    sudo /sbin/chkconfig mysqld on

You can further configure this with the GUI and turn off unnecessary items

    system-config-services

#### Reboot the computer

    sudo reboot

[< Instructions for installing CentOS on your computer](/appion/Appion_Manual/Complete_Installation/Instructions_for_installing_CentOS_on_your_computer) | [Database Server Installation >](/appion/Appion_Manual/Complete_Installation/Database_Server_Installation)
