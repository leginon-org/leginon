## Install the additional package repositories

Unlike RHEL/CentOS, Fedora comes with an Extras repository by default that contains all of the open source software needed by Appion/Leginon.

That said, there are several additional Fedora repositories that you can install. These repositories provide additional packages that are not allowed in the default Fedora package list, such as patented software (MP3 and Movie players), closed source applications (Nvidia video driver, Flash plugin, Adobe acrobat reader). But some repositories install packages over other packages, which can cause problems and conflicts (ATrpms is especially bad at this), so avoid these repositories. So, we recommend only installing RPM Fusion.

### RPM Fusion (optional)

-   http://rpmfusion.org/
-   good for mp3, movies, the nvidia driver and other patent limited software

Download repository rpms and install

    sudo rpm -Uvh http://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-stable.noarch.rpm
    sudo rpm -Uvh http://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-stable.noarch.rpm

## Update current packages

Update the updater to make life easier

    sudo yum -y update yum

### Update all packages

    sudo yum -y update

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
-   **MRC tools**: php-devel gd-devel re2c fftw3-devel php-gd
-   **UCSF Chimera imaging**: xorg-x11-server-Xvfb xorg-x11-drv-nvidia

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
    xorg-x11-drv-nvidia

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

[< Instructions for installing Fedora on your computer](/appion/Appion_Manual/Complete_Installation/Instructions_for_installing_Fedora_on_your_computer) | [Complete Installation ^](/appion/Appion_Manual/Complete_Installation)
