[TOC]

## 1 Get the Eclipse executable

First, you can try the executable that already has the plugins installed. Get [eclipse.tar.gz](http://emg.nysbc.org/redmine/attachments/download/8/eclipse.tar.gz). Just copy it to your machine, uncompress it and the executable is available within the eclipse directoy. No further installation steps are required.

If you want to install things yourself, this is what you need:

1.  Download eclipse from [here](http://www.eclipse.org/downloads/download.php?file=/technology/epp/downloads/release/galileo/SR1/eclipse-jee-galileo-SR1-linux-gtk-x86_64.tar.gz).
2.  Get the plugins:
    1.  Subversion
    2.  PHP
    3.  Subversion connector
    4.  pydev
3.  Copy it to somewhere on your local machine.
4.  Double click the eclipse executable to open. If using a machine that was setup with the AMI kickstart program, you will need to update java to use the 64 bit version.

See also: [PHP: Debugging with Eclipse](http://www.youtube.com/watch?v=zlHUCAf7oSk)

## 2 Create a Workspace and get the MyAMI code from Subversion

1.  Double click the eclipse executable found in the eclipse directory.
2.  When it opens, it will prompt you to choose a workspace. This workspace will hold a local copy of the myami code for you to work on. A good workspace location is a amiworkspace in your home directory. That is /home/username/amiworkspace.
3.  From the menu, select Window -> Open Perspective -> SVN Repository Exploring. This will open a view labeled SVN Repositories.
4.  Go to File -> New -> Repository Location.
5.  In the URL field type: http://emg.nysbc.org/svn/myami to get the Appion and Leginon code.
6.  Press the Finish button at the bottom of the dialog. A new repository will appear in the SVN Repositories view.
7.  Click on the arrow next to the repository icon to view the trunk, branches and tags associated with the repository.
8.  Click on the trunk to highlight it. Right click and select Checkout. This will get the code from the repo and put it in your workspace. When the operation completes, you will find a myami directory under amiworkspace in your home directory.

## 2.1 Import an existing project into a workspace

1.  open the PHP or pydev view
2.  right click and select import
3.  under General select Existing Projects into Workspace
4.  select the project
5.  after the workspace is loaded, if the project is not linked to SVN, select Team->Share Project and select the repository

## 3 Configure your Development Environment

There are 2 types of development that you will most often do with the MyAMI code, Python for core processing and PHP for the web interface.

### 1 Setup the Python environment

Go to Window -> Preferences -> PyDev -> Editor -> Interpreter -- python. Press the Auto Config button then press OK.

### 2 Setup the PHP environment

There are two ways to view the web applications that you are developing in your home directory. If you are developing on a machine that does not have a local Apache server, you can use the Cronus3 web server. The advantage of this is that all the image processing plugins are already installed on Cronus3 so you don't have to worry about them and you don't have to worry about making Apache work. If you do run Apache locally, you can take advantage of integrated debugging tools in Eclipse and learn more about how all the pieces of the project fit together since will will have to set more things up.

Also note that the directions below will not get project_tools running. It is currently undergoing many changes and directions will be added when that process is complete.

#### Use Cronus3 or Fly to view your web app

Follow [Use Cronus3 or Fly to view your web app](/appion/Use_Cronus3_or_Fly_to_view_your_web_app)

#### Create your config file

Use the setup wizard to create the config file by browsing to myamiweb/setup.
At AMI, you would go to cronus3/~YOUR_HOME_DIR/myamiweb/setup.

**IMPORTANT:** Never check your local copy of the config files into Subversion. We don't want to share our database user information with the world. You can right click on the config file and select team -> svn:ignore to tell svn to ignore this file.

1.  To edit the config file by hand:
    1.  Change directories to the myamiweb project: **$ cd ~/amiworkspace/myami/myamiweb**
    2.  Copy config.php.template to config.php: **$ cp config.php.template config.php**
    3.  Open config.php for editting: **$ vi config.php**
    4.  Make changes similar to this [example config file](/appion/Developers_guide/AMI_Eclipse_Quick_Start_Guide/Example_config_file), replacing "amber" with your home directory.

#### Use your local Apache server to view your web app (optional)

1.  Make sure you are logged in as root. ($ su)
2.  Make sure Apache is installed. There should be /etc/init.d/httpd on your machine. Start apache with $ /etc/init.d/httpd start.
3.  Point a web browser to http://localhost/ and make sure you see the apache test page.
4.  Make sure Apache is configured for php
5.  the Apache config file is at /etc/httpd/conf
6.  web files should be at /var/www/html
    1.  create symbolic link to your workspace in /var/www/html
    2.  Try to view at http://localhost/myamiweb
    3.  Not working because need the files on phpami
        1.  go to phpami in your myamiweb workspace and create symbolic links to each file that remove the .php file extension
        2.  put a symbolic link to this folder from user/share ( $ ln -s /home/amber/amiworkspace/myami/phpami php )
7.  To debug PHP issues check http://localhost/myamiweb/info.php
8.  For everything to work, you need to install plugins like the MRC module

## 4 Get a local copy of the databases (optional)

If you want to work on the databases and you would prefer to have a local copy to play with, read [How to set up a local copy of AMI databases](/appion/Developers_guide/Setup_Local_Databases_).

You also have an option of creating a copy of the database that you wish to work with on the fly server. You will name your DB with your name prepended to the name of the DB that is copied. You will need to update your Config file accordingly. You can work with your DB without affecting formal testing on fly or the production databases.

## 5 Run a Python Script

1.  Change perspective to PyDev. (Window->Open Perspective)
2.  Right click on the myami project and choose Properties
3.  Select PyDev - PYTHONPATH
4.  Under Source Folders select Add source folder
5.  Make sure myami is selected and press OK
6.  Build numextension
    1.  Right click on numextension/setup.py and select Properties
    2.  Select Run/Debug settings
    3.  Select Edit
    4.  Select the Arguments tab
    5.  Under program arguments type *build*
    6.  Select OK
    7.  Right click on setup.py and select Run As->Python Run
7.  Run Leginon
    1.  Make sure the config files are set correctly (leginon.cfg, sinedon.cfg)
    2.  Run leginon/syscheck.py by right clicking and selecting Run As->Python Run
    3.  Right click on leginon/start.py and select Run As->Python Run

## 6 Merge a revision to another branch

1.  Commit your change and note the revision number.
2.  Go to the branch that you want to merge the code into and select Team->Merge.
3.  Under URL click Browse and select the trunk or branch that you already committed your changes to.
4.  In the revisions area, select the radio button next to Revisions: and click the Browse button.
5.  Select the revision that you wish to merge AND the revision immediately preceding yours.
6.  Select OK to close out the revision browser.
7.  Select the Preview Button to see what files will be merged.
8.  If it looks like the correct files, select the Ok button the close the preview and select OK again to execute the Merge.
9.  When it completes, Eclipse will open a synchronizing window where you can see the differences between your local, merged version of the files and the version held by SVN.
10. If all the changes look correct, you may Commit the changes. Please include a comment in the commit message similar to the following:

> Merge from trunk r14376 and r14383 to 2.0 branch, Fix for Post-processing does not work with FREALIGN jobs , refs #657

## 7 How to commit a change to svn

1.  In the Pydev Explorer or PHP explorer view, right click on the file, folder or project that you want to commit and select Team->Synchronize with repository. This will show you what files have been changed in your local sandbox.
2.  You may click on the changed files to view the specific differences that you will be checking in to ensure they are what you intended.
3.  Then right click and select Commit. Add a comment that references the redmine issue number (ex. refs #123). This will automatically link the revision number to the issue in redmine.
