[TOC]

**Appion Install Manual Referenced to Leginion Installation**

=

*The Appion Team*

email: **appion@scripps.edu** for any help you need.

## 1. Introduction

This document describes a general installation of Appion, concentrating on the installation and setup on the database and web servers. Most sections refer to the Leginon installation documentation since the two share the same general architecture. If you want to run real Leginon on the microscope, you just need to follow the additional installation starting from [Processing Server Window Installation Chapter of Leginon installation manual](http://emg.nysbc.org/documentation/leginon/bk02ch04s08.php).

## 2 Setup MySQL databases

### see [Leginon database server-side installation manual](http://emg.nysbc.org/documentation/leginon/bk01ch04s07.php) for details, including how to increasing cache size.

### Preliminary steps if you have an existing project database from a previous installation

We need to remove a table in the project database called "install". This will allow the new default tables to be defined when we set up on the web-server side.

    $ mysql projectdata -u usr_object
    mysql> drop table install;
    mysql> exit

### Additional work

You need to decide what prefix you will use for the processing databases. We will be creating them on the fly later. Our default is **ap** followed by a project id number. More about this later.
At this point, you need to do the following to grant privileges to users for any database whose name starts with **ap**

    $ mysql -u root -p

Note: If you didn't set a mysql root password, don't use -p option.

    mysql> GRANT ALL PRIVILEGES ON `ap%`.* TO usr_object@"%";
    mysql> exit

## 3 Web server side installation

[Web Server Installation](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation)

**TODO:** The following steps are most likely no longer needed here:

### Follow instructions in [Leginon Database server-side installation manual](http://emg.nysbc.org/documentation/leginon/bk01ch04s07.php).

### Continue with the instructions in [Leginon Web server set up and Installation](http://emg.nysbc.org/documentation/leginon/bk02ch04s08.php).

### Additional work

-   Edit project`_`1`_`2/config.php to assign the same prefix to your processing db as defined in your MySQL setup.


    $DEF_PROCESSING_PREFIX = "ap";

-   Enable the processing plug-in by uncommenting out the following line in the file`myamiweb/config.php`


    addplugin("processing");

-   Copy `myamiweb/processing/config_processing.php.template` to `myamiweb/processing/config_processing.php`
-   Edit `myamiweb/processing/config_processing.php`


    $PROCESSING_DB_HOST = "your_db_host";
    $PROCESSING_DB_USER = "usr_object";
    $PROCESSING_DB_PASS = ""; 
    $PROCESSING_DB = "";

Remember that the last line should be kept empty as this will be set dynamically.

We will not include the processing host or cluster registration now. It is covered in the last part of this document.

## 4 Create a test project and processing database

### Follow the instructions on [how to create new project](http://emg.nysbc.org/documentation/leginon/bk02ch06.php) in the Leginon Manual.

### Additional work

1.  Click on a project name on the webpage `http://your_host/project_1_2/project.php`. This will take you to a new webpage `http://your_host/project_1_2/getproject.php?pId=1`. The number following "pId=" depends on the project id automatically assigned to the project.
2.  At the end of the Info table, you should see:


    processing db: not set (create processing db) db name ap1

You can create the default numbered style database ap... or give it a new name with the same prefix. If you want to specify a database name that does not use the default prefix, please note that your db user specified in the config.php in project_1_2 needs to have the necessary privileges for that database. You may additionally want to change the value assigned to $DEF_PROCESSING_PREFIX in project_1_2/config.php if you want to use your new prefix all the time.

1.  Enter the processing database name and click "create processing db".
2.  The page should refresh and display the linked database like this:


    processing db: ap1

See next section on trouble shooting if you get the original page instead.

-   **Repeat the above process for all your projects.**

If you want all your processing databases combined in one single database (not recommended, as this becomes large very fast), just use the same name for all your projects.

The above procedure not only creates the database, but also create some of the tables that you need to start processing.

### Trouble Shooting

If the 'getproject.php' webpage remains unchanged, your processing database link is not accepted. This is usually
caused by an incorrect setting such as:

1.  The mysql user does not have the privileges to create the named database.
    See Section-5.3 on what you should do. To try it again after your mysql correction, you should repeat Section-5.2 to allow reinitialization from the project_1_2 web page and then try 7.2 again.
2.  You have accessed an earlier version of project web page after you reinitialized the install table in your existing project database.
    The install table in the project database is set to deny further changes once any project web page is accessed. As a result, required table property changes and new table insertion would fail.
    Here is how to fix it:
3.  Repeat Seciont-5.2 to allow reinitialization.
4.  Try Section-7.2 again.

## 5 Processing server side installation

### Follow [Leginon processing-server-side installation on Linux](http://emg.nysbc.org/documentation/leginon/bk02ch04s05.php)

### Additional work

-   Go to your Leginon installation directory (typically /usr/lib/python2.4/site-packages/Leginon/)
-   Edit project.py. Change line 5 to:


    use_processingdb_table = True

-   Add the appionData module to sinedon.cfg, which you have already modified during the Leginon installation.


    [appionData]
    user:   usr_object

**[]{lang="Note"}** The module names in brackets are case sensitive and need to be exact.
The user name needs to match the name for which privileges have been granted on the `ap%` databases.

### Download and install pyappion

#### Install prerequisite processing packages that are not included in the Leginon installation

Find a list of these packages [here](/appion/Appion_Installation_Manual#Packages-not-included-in-the-Leginon-installation).

#### [Download pyappion](http://appion.googlecode.com/files/pyappion-0.5.3-r3665.tgz)

#### [Compile and Setup Instructions](/appion/Start_with_existing_CentOS_installation#5-Compile-and-setup-Appion-python-programs)

### Install external packages

Follow instructions for the individual packages.
Instruction for compiling Xmipp for OpenMPI is [here](/appion/Start_with_existing_CentOS_installation#8-Install-external-packages).

## 6 Initialize Leginon with its admin tools

### DO NOT follow Leginon administration tool instructions. We only need to upload images for appion processing, which is much simpler.

1.  Go to the webpage `http://your_host/dbem_1_5_1/addinstrument.php`
2.  Create a fake TEM instrument like this:


    name: my_scope
    hostname: whatever
    type: Choose TEM

1.  Create a fake CCDCamera instrument like this:


    name: my_scope
    hostname: whatever
    type: Choose CCDCamera

**[]{lang="Note"}** If you use Leginon, and still want to upload non-Leginon images, make sure that you create a pair of fake instruments like these on a host solely for uploading. It will be a disaster if you don't, as the pixelsize of the real instrument pair will be overwritten by your upload.

## 7 Start your first Appion session from the web

### Upload Images to a new session

1.  Go to webpage `http://your_host/dbem_1_5_1/` This is the general starting point for Leginon.
2.  Follow the link for the Project DB (bottom right)
3.  Select your test project, click on the name. This takes you to the same page you created for the processing database.
4.  Below the experiment heading you will find a link that says "upload images to new session". This takes you to your first Appion processing page, where you can use the web gui and instruction to upload your images.
5.  Once all fields are filled in click on "Just Show Command", which will bring you to a page that displays a command line. Copy, paste, and execute this command into your text terminal, which will use the processing server programs and the database behind it.
    **[]{lang="Note"}** All images uploaded in an experiment session should have the same pixel size because they cannot easily be divided into groups during processing.

### Good starting point for future reference

-   If you have been successful so far, the image you uploaded will show up in the viewers. You may choose one of
    the viewers provided by dbem_1_5_1 as your starting point to select your session, to view the images, and to start processing by following the link at the top-left corner called "processing".

## 8 Remote Appion Processing through ssh

A more advanced way to run appion script is done through an ssh session. This is equivalent of having you ssh into a computer and starting the appion processes.

There are two kinds of appion processes. The first is a single-node process that can be run on a stand-alone workstation or the head-node of a computer cluster without PBS. The second is a multiple-node process that requires PBS to run on the cluster. When you use "Just Show Command" option, it is always a single-node process, but if you run through ssh it could be either, depending on the demand of the process. For example,
imageuploader.py is always run as single-node process while maxlikeAlignment.py is either run on single-node with "Just Show Command" or as a PBS job submission when you run through ssh.

### Install and setup ssh2 extension for php at your web-server

This enables an ssh session initialized from appionweb

# Download and install the ssh2 extension for php as instructed at its download site:

-   http://www.php.net/manual/en/ssh2.installation.php
    Install openssl and compile libssh first before compiling php-ssh2 extension. Once you get the final ssh2.so, add it in your php.ini

The extension module is added to php in the same way as does the php-mrc module we distribute for the viewing mrc images through php. To check whether it worked and for alternative way to make php recognize the module used in newer php, see http://emg.nysbc.org/documentation/leginon/bk02ch04s07.php under the section **Check php information** and **Alternative approach if mrc module does not show up in info.php output**

### configuration at web server side

**IMPORTANT**: What we refer here as *your_cluster.php* should not be taken literally. For example, if you access your cluster through network with a name "bestclusterever", you should name your cluster configuration php file **bestclusterever.php**, not *your_cluster.php*.

1.  Go to your_dbem_1_5_1/processing directory
2.  Copy **default_cluster.php** to *your_cluster.php*
3.  [Edit your_cluster.php](/appion/Appion_Manual/Complete_Installation/Setup_Remote_Processing/ClusterPhpSettings) to correspond to your cluster configuration.
4.  Edit **config_processing.php** to add your cluster and, if desired, a stand-alone workstation as processing_host and register the *your_cluster.php* you just created.


    $PROCESSING_HOSTS[]="your_stand-alone_processing_workstation";
    $PROCESSING_HOSTS[]="your_cluster";
    $CLUSTER_CONFIGS= array (
      'your_cluster'
    );

### Setting up PBS on processing server side

Follow these [instructions to set up PBS on your processing server](/appion/Start_with_existing_CentOS_installation#9-Install-a-PBS-job-submission-system).

### Testing

#### Testing php-ssh2 installation

Check your info.php as you did with mrctool installation. Corrected installed extension should show up in the output of info.php. Reference http://emg.nysbc.org/documentation/leginon/bk02ch04s07.php under the section **Check php information** and **Alternative approach if mrc module does not show up in info.php output**.

#### Testing ssh log in

Use the top right form on the processing page to log in as if doing an ssh session. The page will acknowledge that you have been logged in if the setup is correct. You will be able to edit description of a run and to hide failed runs when logged in. The option for submitting the job appears at the bottom of the processing form whenever available.

#### Testing simple appion processing job submission

Upload template is a good example to try:

1.  Create a small mrc image as your template to be uploaded.
2.  Select Upload template in Import tools in the appionweb processing menu of an existing session.
3.  Type in the needed information.
4.  When you finish filling the form, instead of clicking on "Just show command", choose your processing host and run the job by clicking "Upload Template".
5.  For simple process such as this, the webpage will take a little while to refresh until the job is completed.
6.  If you get the message "Template is uploaded", the process is successful and if you refresh the page you will find the template in the available list.

#### Testing PBS-required appion processing job submission

Particle selection such as DogPicker is a good example to try:

1.  Click on DoG Picking under Particle Selection menu
2.  Enter the required parameters
3.  When you finish filling a form for an appion processing, choose your processing host and run the job. Pages for monitoring the job become available after the job is queued and subsequently begins running. If the status appears as "Running or Queued" at first, the setup is likely correct.
4.  After a while, the process will be completed and the status becomes "Done" when you click to have the Status updated on the page.

#### Check *your_cluster.php* setup

For reconstructions involving iterations of different parameters such as EMAN reconstruction by refinement, the *your_cluster.php* is used to generate the script. Examine the script created on the web form and modify *your_cluster.php* You can copy the script to your cluster and test run/modify it until it is correct.
