Computer(s) used for the whole Leginon system need to support five functions:

1.  TEM/Camera control and data output (by python-side packages of Leginon
    system)
    **Note:** The computer(s) attached to the microscope/camera is used for this function. Therefore, it is on a Windows os.
2.  General Leginon operation such as target selection and image processing (processing
    server of Leginon system)
3.  Image data storage.
4.  Other meta-data storage through MySQL database (by database server of Leginon
    system)
5.  Web server (using PHP-side of Leginon system).
6.  Direct detector movie frame alignment processing server. For the popular MotionCorr and MotionCor2, this needs to have multiple gpus dedicated for processing.

The six functions can be distributed to six different computers on a network or all on
one single computer (with web server not viewing the images). However, since the latter minimal setup requires the use of the computer
attached to the microscope and digital camera for all functions, it is not advisable.

Processing server of Leginion is a multi-platform software, meaning it can run on both
Microsoft Windows and [Linux](/leginon/Leginon_Manual/Complete_Installation/Select_Linux_distribution_to_use), although we and others have found that Windows have trouble managing its memory for such a demanding task. MySQL used in the database server is also supported by multiple platforms.
The following examples show several arrangements that take advantage of distributed system.
Other combinations are possible, but will basically be variations on one of the following
themes.

See special notes on [Using Leginon on a system where the microscope and camera are controlled by different computers](/leginon/Using_Leginon_on_a_system_where_the_microscope_and_camera_are_controlled_by_different_computers) if it applies to you.

## Configuration A

-   One or more Windows computer that controls the Microscope and your digital camera ; 1 Linux computer (for all
    other functions, separate from the Microscope) (Good for single user and small-scale
    acquisition)*

### On the microscope/camera computer(s):

-   Install the latest processing server side of Leginon release (and supporting
    packages) following [Installation on the microscope computer](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_microscope_computer)

### On the Linux computer:

-   Install the full Leginon package including the processing, database, and web server.
    The easiest is to use [Autoinstaller for CentOS](/leginon/Leginon_Manual/Complete_Installation/Autoinstaller_for_CentOS)
    For manual installation, follow full instruction in this chapter.
    See [Minimum Requirements and current NRAMM setup](/leginon/Leginon_Manual/An_Introduction_to_Leginon/Minimum_Requirements_and_current_NRAMM_setup)

### For an example of this configuration for Krios/K2 combination, see [here](/leginon/Leginon_Manual/An_Introduction_to_Leginon/Minimum_Requirements_and_current_NRAMM_setup/Minimum_Requirements_for_frame-saving_direct_detectors)

## Configuration B

*One or more Windows computers that control the microscope and your digital camera ; 4 Linux computers (one for
each function) (Good for multiple microsopes, users and large-scale acquisition)*

This is the set-up at NRAMM. It has the processing server side of Leginon installed on
the Windows computer attached to the microscope and on the Linux computer that is used for
running Leginon. A second Linux machine is dedicated to the database while the web-based
viewer is hosted by another server, and a third Linux machine specialized as the database server.

-   Install the python-side Leginon (and supporting packages) on the Windows computer(s)
    controlling the microscope/camera and on the Linux computer that is to run Leginon. You can
    make the latter installation accessable to any numbers of linux computers on your
    network.


-   Install full processing server side of Leginon on a Linux computer, typically in the scope room
    for setup convenience.
-   Install MySQL on a Linux computer served as the database server


-   Install PHP, the Apache Web Server, and PHP-side of Leginon system on the third Linux
    computer that will serve as the web server host.


-   For each additional scope/camera pair, add a linux computer for the processing purpose.


-   The computer hosting the data storage should be accessable by all linux
    boxes.

The data storage may be on one of these computers that is accessable by the web and the processing
computers.

### See [Current NRAMM setup](/leginon/Leginon_Manual/An_Introduction_to_Leginon/Minimum_Requirements_and_current_NRAMM_setup/Current_NRAMM_setup) and [SEMC file storage policy](/leginon/Leginon_Manual/An_Introduction_to_Leginon/Minimum_Requirements_and_current_NRAMM_setup/SEMC_file_storage_policy) 

[< What is in this Chapter](/leginon/Leginon_Manual/Complete_Installation/What_is_in_this_Chapter) | [What Linux distribution should be used? >](/leginon/Leginon_Manual/Complete_Installation/Select_Linux_distribution_to_use)
