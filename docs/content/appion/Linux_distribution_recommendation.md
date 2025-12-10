We list our experience and current progress here.

## Our Preference : CentOS

If you have a new computer(s) for your Leginon/Appion installation, we recommend installing CentOS because it is considered to be more stable than other varieties of Linux.

CentOS is the same as Red Hat Enterprise Linux (RHEL), except that it is free and supported by the community.

We have most experience in the installation of the supporting packages on CentOS and this installation guide has specific instruction for the process.

Leginon and Appion version 3.0, and the development trunk run on CentOS 6.x.

Start at [Instructions for installing CentOS on your computer](/appion/Appion_Manual/Complete_Installation/Instructions_for_installing_CentOS_on_your_computer).

## Other known cases of success:

### Fedora 19

-   Database server - Works
-   Processing server - Works
-   Web server - Works

Start at old documentation of [appion:Instructions for installing Fedora on your computer](/appion/appionInstructions_for_installing_Fedora_on_your_computer) and search Leginon Forums for the word "Fedora" for trouble shooting.

### SuSE, Ubuntu

success with this instruction: [Myami installation on Ubuntu](/appion/Linux_distribution_recommendation/Link_to_ubuntu).

### MacOS (10.9)

-   Database server - Works
-   Processing server - Most bits working on MacOSX, but some of the appion python libraries contain ancient Fortran code that does not compile easily on a Mac
-   Web server - Works but not with the bundled 5.4 due to jpeg support problem of php-gd.
