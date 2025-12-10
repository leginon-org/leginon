Before you start, make sure you have CentOS 6 installed on your computer. Note that upgrading from CentOS 5 to CentOS 6 might damage existing filesystems and operating systems as described in [CentOS Migration Guide](http://wiki.centos.org/HowTos/MigrationGuide). That's why we recommend starting with a fresh install of CentOS 6. The following links provide excellent step by step guide on how to install CentOS 6 Linux from scratch on a new machine:

-   http://linuxmoz.com/how-to-install-centos-6-linux-for-servers-desktops
-   http://www.if-not-true-then-false.com/2011/centos-6-netinstall-network-installation

In the package selection step switch from Minimal to Web Server.

![](http://linuxmoz.com/images/c6i/install-centos-6-minimal-install.png)

#### Disable SELinux and Firewall

To disable [SELinux](http://wiki.centos.org/HowTos/SELinux):

1.  Edit file "/etc/selinux/config"
2.  Change "SELINUX=enforcing" to "SELINUX=disabled"
3.  Save the file
4.  Restart your computer

To disable firewall run *system-config-firewall-tui* command and use Space key to unchecked the checkbox next to Enabled.

### Install Extra Packages for Enterprise Linux (EPEL)

    rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm

Note that release version (6-8) is the current release at the time of this writing. Please visit http://fedoraproject.org/wiki/EPEL/FAQ#How_can_I_install_the_packages_from_the_EPEL_software_repository.3F for more up-to-date information on how to install the packages from the EPEL software repository.

    yum install php-gd gcc libssh2-devel php-pecl-ssh2 mod_ssl php-mysql php-devel php fftw3-devel python-imaging python-devel mod_python scipy svn
    easy_install fs PyFFTW3

### [Configure php.ini](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation/Configure_phpini)

Edit /etc/php.ini and change line ~229 to

    short_open_tag = On

Note that short_open_tag appears twice in /etc/php.ini and you need to set [short_open_tag = On](http://www.apachefriends.org/f/viewtopic.php?p=155513) at around line 229 for it to take effect.

### Start Apache HTTP Server

    service httpd start
    chkconfig httpd on

See also: [How to start Apache at Startup on Centos or Red Hat Enterprise Linux using chkconfig](http://thevagabondgeek.com/12-how-to-start-apache-at-startup-on-centos-or-red-hat-enterprise-linux-using-chkconfig).

If you have a file server that stores Appion and Leginon session, start and enable nfs services as well:

    service nfs start
    chkconfig nfs on

See [How to Set Up an NFS Mount on CentOS 6](https://www.digitalocean.com/community/articles/how-to-set-up-an-nfs-mount-on-centos-6)

### [Download Appion and Leginon Files](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Download_Appion_Files)


svn co http://emg.nysbc.org/svn/myami/branches/myami-3.2


### [Install Redux image server](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation/Install_Redux_image_server)

    cd myami
    ./pysetup.sh install
    mkdir /etc/myami
    cp redux/redux.cfg.template /etc/myami/redux.cfg
    /etc/init.d/reduxd start

### [Install the Web Interface](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation/Install_the_Web_Interface)

    cp -r myamiweb/ /var/www/html/ 

Visit http://localhost/myamiweb/setup and follow instructions in Web Tools Setup Wizard.

See also [Install the Web Interface Advanced](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation/Install_the_Web_Interface/Install_the_Web_Interface_Advanced).
