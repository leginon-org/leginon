## Why Fedora?

If you have a new computer(s) for your Leginon/Appion installation, Fedora is a cutting edge system that has all the latest and greatest feature.
While Fedora is great for a desktop computer, it can be a hassle for a server. Fedora recommends that you upgrade the computer every 6 months and all but requires a upgrade every year. With servers you like things to remain the same for longer periods of time, this is not Fedora. Fedora always has the latest versions. If you want something more stable we recommend installing CentOS. See [Instructions for installing CentOS on your computer](/appion/Appion_Manual/Complete_Installation/Instructions_for_installing_CentOS_on_your_computer)

Fedora is a cutting edge distribution produced by a community of programmers that is maintained by Red Hat.

## Download the DVD iso disk of Fedora 13

# DVD iso files are available at
## http://fedoraproject.org/en/get-fedora-options
# In the section, Fedora 13 DVD, click on i386 for 32bit machines or x86_64 for 64bit machines
# Download the 64bit 'Fedora-13-x86_64-DVD.iso' file

    wget -c http://download.fedoraproject.org/pub/fedora/linux/releases/13/Fedora/x86_64/iso/Fedora-13-x86_64-DVD.iso


# Download the 32bit 'Fedora-13-x86_64-DVD.iso' file

    wget -c http://download.fedoraproject.org/pub/fedora/linux/releases/13/Fedora/i386/iso/Fedora-13-i386-DVD.iso

## Confirm download went correctly

perform a SHA256SUM confirmation:

    sha256sum Fedora-13-x86_64-DVD.iso
    dab657e1475832129ea3af67fd1c25c91b60ff1acc9147fb9b62cef14193f8d2

The result should be the same as in the sha256sum file provided by Fedora:

-   http://download.fedoraproject.org/pub/fedora/linux/releases/13/Fedora/x86_64/iso/Fedora-13-x86_64-CHECKSUM for 64bit
-   http://download.fedoraproject.org/pub/fedora/linux/releases/13/Fedora/i386/iso/Fedora-13-i386-CHECKSUM for 32bit

## Burn DVD iso file to DVD disk

Use dvdrecord in Linux to burn disk

    dvdrecord -v -dao gracetime=10 dev=/dev/dvd speed=16 Fedora-13-x86_64-DVD.iso

> The `/dev/dvd` may not link to your DVD drive on my machine it was called `/dev/dvd1`. Do a `ls /dev/dvd*` to look for alternate names

## Install Fedora 13 with default packages

* Setup network, root, password as desired
* This install will assume that only **"Graphical Desktop"** to be selected
* More information available at [http://docs.fedoraproject.org/en-US/Fedora/13/html/Installation_Guide/index.html Fedora Install Documentation]

> Note: In one case we had to use the option "Install with basic video driver", because after doing the normal install the screen went blank and it was not usable.

## Add yourself to the sudoers file

Make sure you have root permission.
Open the file in an editor. ex. vi /etc/sudoers
Look for the line:

    root    ALL=(ALL)   ALL

Add this line below the root version:

    username    ALL=(ALL)   ALL

Logout and log back in with your username.

Your Fedora installation is complete.

[Download additional Software (Fedora Specific) >](/appion/Download_additional_Software_Fedora_Specific)
