## Why CentOS?

If you have a new computer(s) for your Leginon/Appion installation, we recommend installing CentOS because it is considered to be more stable than other varieties of Linux.

CentOS is the same as Red Hat Enterprise Linux (RHEL), except that it is free and supported by the community.

We have most experience in the installation on CentOS and this installation guide has specific instruction for the process.

see [Linux distribution recommendation](/appion/Appion_Manual/Complete_Installation/Select_Linux_distribution_to_use) for more information on Operating System choices.

## CentOS Installation Resources

Note that upgrading from CentOS 5 to CentOS 6 might damage existing filesystems and operating systems as described in [CentOS Migration Guide](http://wiki.centos.org/HowTos/MigrationGuide). That's why we recommend starting with a fresh install of CentOS 6. If you need more details on how to install CentOS than we provide here, the following links provide excellent step by step guide on how to install CentOS 6 Linux from scratch on a new machine:

-   http://linuxmoz.com/how-to-install-centos-6-linux-for-servers-desktops
-   http://www.if-not-true-then-false.com/2011/centos-6-netinstall-network-installation

## Download the ISO disk of CentOS

**Latest version tested at NRAMM:**

-   CentOS 5.8 for Leginon/Appion 2.2
-   CentOS 6.3 for Leginon/Appion 2.2-redux and 3.0
-   CentOS 6.7 for Leginon/Appion 3.2+ and trunk

**Note:** Formally released versions of Appion at versions 1.x and 2.x run on CentOS 5.x. except 2.2-redux, which has the same features as 2.2, but runs on CentOS 6.x.

# ISO files are available at
## http://wiki.centos.org/Download
## http://mirrors.kernel.org/centos/
# Click on i386 for 32bit machines or x86_64 for 64bit machines
# Pick a mirror and download the appropriate file such as 'CentOS-5.8-i386-bin-DVD-1of2.iso '

## Confirm download went correctly

Perform a SHA1SUM confirmation:

    sha1sum CentOS-5.8-i386-bin-DVD-1of2.iso

The result should be the same as in the sha1sum file provided by CentOS. This is found at the same location you downloaded the .iso file.
For example:

-   http://centos.mirrors.tds.net/pub/linux/centos/5.4/isos/x86_64/sha1sum.txt for 64bit
-   http://centos.mirrors.tds.net/pub/linux/centos/5.4/isos/i386/sha1sum.txt for 32bit

## Burn ISO file to DVD disk

Use dvdrecord in Linux to burn disk.

    dvdrecord -v -dao gracetime=10 dev=/dev/dvd speed=16 CentOS-5.8-i386-bin-DVD-1of2.iso 

## Install CentOS with default packages

* Setup network, root, password as desired
* This installation guide assumes that **"Software Development Workstation"** is selected during the package selection step
* More information available at [http://wiki.centos.org/Documentation CentOS Documentation]

## Add yourself to the sudoers file

**Note:** This step is optional, however you will need root access to complete the Appion Installation.

Make sure you have root permission.
Open the file in an editor. ex. vi /etc/sudoers
Look for the line: root ALL=(ALL) ALL.
Add this line below the root version:

    your_username ALL=(ALL)       ALL

Logout and log back in with your username.

## Disable SELinux and Firewall

To disable [SELinux](http://wiki.centos.org/HowTos/SELinux):

1.  Edit file "/etc/selinux/config"
2.  Change "SELINUX=enforcing" to "SELINUX=disabled"
3.  Save the file
4.  Restart your computer

To disable firewall run *system-config-firewall-tui* command and use Space key to unchecked the checkbox next to Enabled.

The CentOS installation is complete.
