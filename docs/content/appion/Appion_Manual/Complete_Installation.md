There are three main components of the Appion system: a Database Server, a Processing Server and a Web Server. These may be installed on separate computers, or on the same computer. Several installation options are listed below. If you are unsure which installation option to choose for your situation, please inquire on the [Software Installation Forum](http://emg.nysbc.org/redmine/projects/leginon/boards/15). There are also [instructions to register for a Redmine account](/appion/AMI_Redmine_Quick_Start_Guide) which is needed to make a Forum post.

## Automatic Installation Script:

The Automatic Installation Script installs a fully functional demo version of Appion. This script is intended to be used with a single computer running a fresh installation of the CentOS operating system. The process is very quick and easy and includes groEL images for you to begin processing right away.

The script does not install any gpu-based external pacakges. You will have to do that yourself.

This installation does everything as root. If you are to use this for production and don't want to be root all the time, a few changes is required after the installation is tested out.

1.  [Install using the auto-installation tool](/appion/Appion_Manual/Complete_Installation/Install_using_the_auto-installation_tool)
2.  [Changes to auto-installed appion for production usage](/appion/Appion_Manual/Complete_Installation/Changes_to_auto-installed_appion_for_production_usage)
3.  [This table](/appion/Processing_Server_External_Packages_Installation/Package_executable_alias_name_in_Appion) will help you link your installation to alias that appion scripts looks for if you have your own external package installed.

## Manual Installation Instructions:

The Manual Installation Instructions are intended for a production system. We recommend using the CentOS operating system, but we include instructions for Fedora under the Alternative Options below. Also under Alternative Options you will find instructions for installing Appion with an existing Leginon installation.

1.  [Select Linux distribution to use](/appion/Appion_Manual/Complete_Installation/Select_Linux_distribution_to_use)
2.  CentOS Installation:
    1.  [Instructions for installing CentOS on your computer](/appion/Appion_Manual/Complete_Installation/Instructions_for_installing_CentOS_on_your_computer)
    2.  [Download additional Software (CentOS Specific)](/appion/Appion_Manual/Complete_Installation/Download_additional_Software_CentOS_Specific)
3.  [Database Server Installation](/appion/Appion_Manual/Complete_Installation/Database_Server_Installation)
4.  [File Server Setup Considerations](/appion/Appion_Manual/Complete_Installation/File_Server_Setup_Considerations)
5.  [Processing Server Installation](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation)
6.  [Web Server Installation](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation)
7.  [Additional Database Setup After Web Server Initialization](/appion/Appion_Manual/Complete_Installation/Additional_Database_Server_Setup_after_Web_Server_Installation)
8.  [Setup Remote Processing](/appion/Appion_Manual/Complete_Installation/Setup_Remote_Processing)
9.  [Create a Test Project](/appion/Appion_Manual/Complete_Installation/Create_a_Test_Project)
10. [Security Considerations](/appion/Appion_Manual/Complete_Installation/Security_Considerations)

## Alternative Options:

1.  Fedora Installation:
    1.  [Instructions for installing Fedora on your computer](/appion/Appion_Manual/Complete_Installation/Instructions_for_installing_Fedora_on_your_computer)
    2.  [Download additional Software (Fedora Specific)](/appion/Download_additional_Software_Fedora_Specific)
2.  [Installing Appion with an existing Leginon installation](/appion/Appion_Manual/Complete_Installation/Installing_Appion_with_an_existing_Leginon_installation)

## Troubleshooting your installation:

1.  [Installation Troublshooting Guide](/appion/Appion_Manual/Complete_Installation/Installation_Troublshooting_Guide)

_

[< Version Change Log](/appion/Appion_Manual/Version_Change_Log) | [Upgrade Instructions >](/appion/Appion_Manual/Upgrade_Instructions)
