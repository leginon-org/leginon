The changes from v1.5 requires update of all in-house components of Leginon and dbemtools,
but not the database nor mrctools. instruments.cfg should be modified on each microscope host.
Don't forget that you need to also update the packages on the microscope-controlling computer
since the pyScope update need to be synchronized.

See Installation Troubleshooting and the [Leginon Forum](http://emg.nysbc.org/redmine/projects/leginon/boards/6) searching
for "install" if you run into problems.

## Packages required from NRAMM

Here are the packages you need to install with python installer

  SVN Package Name   Installed Python Package Name   Reason for update:
  ------------------ ------------------------------- -------------------------------------
  numextension       numextension                    none
  libcv              libCV                           bug fixes
  leginon            Leginon                         new features
  pyami              pyami                           clean up
  sinedon            sinedon                         new stuff
  pyScope            pyScope                         new instrument configuration
  ImageViewer        ImageViewer                     updated and required for tomography

## Download and install SVN client program:

By switching to svn package check out, you now need to install svn client. The rpm
package probably has the word "svn" or "subversion" in its name.

## Check out SVN Source Files from the depository

From a text
terminal:

    mkdir Leginon-1.6-ALL
    cd Leginon-1.6-ALL
    svn co http://emg.nysbc.org/svn/leginon/branches/1.6 Leginon
    svn co http://emg.nysbc.org/svn/pyami/branches/leg1.6 pyami
    svn co http://emg.nysbc.org/svn/pyScope/branches/leg1.6 pyScope
    svn co http://emg.nysbc.org/svn/sinedon/branches/leg1.6 sinedon
    svn co http://emg.nysbc.org/svn/numextension/branches/leg1.6 numextension
    svn co http://emg.nysbc.org/svn/libcv/branches/leg1.6 libcv
    svn co http://emg.nysbc.org/svn/ImageViewer/branches/leg1.6 ImageViewer

## Perform system check:

In addition to the downloads from our svn depository, there are several other
requirements that you will get either from your OS installation source, or from its
respective website. The system check in the Leginon package checks your system to see if you
already have these requirements

    cd Leginon
    python syscheck.py

You should have all the supporting packages installed for v1.5. If you see any lines
like "* Failed...", then you have something missing. Otherwise, everything should result
in "OK". Note that numpy and scipy are now required by the new version even if you don't run
tomography. numarray is no longer used.

## Uninstall your existing packages:

At the beginning of the syscheck.py output, the location of the exisiting Leginon folder
is shown. Although new installation overwrite the old in most cases, problem has been
observed in the past. Therefore, it is best to remove the old files before new
installation.

For example, your Leginon folder is at /usr/lib/python/site-packages/Leginon

    cd /usr/lib/python/site-packages
    rm -r Leginon

Be aware that in some cases the installed package name is different (capitalized) from
your svn package name and that numextension amd libCV are not in its own subdirectory in the
python library but just the compiled .so files

## Install the packages you downloaded from NRAMM svn depository

-   run syscheck.py again to make sure you have everything.


-   Reinstall the package in each folder with commands such as
        cd leginon
        python setup.py install

## Modify sinedon.cfg if you use grid-inserting robot

* Find your sinedon.cfg. Depending on your previous setting, look in the
directories listed here in order:
*your home directory as described in syscheck.py
*The sinedon directory where it is called from. If unsure, start python command
line and type these to find
out:

    python> import sinedon
    python> sinedon

-   Add the following database configuration. The Robot2 module uses the database to
    communicate to the robot. Applications that carries the name "Robot" requires this to be
    set. In general, using the same database as the general leginon database is fine.


    [robot2]
    db: dbemdata

## Transfer Drift adjustment preference to use Transform Manager

* This procedure copies all most recent user settings to that required by the new
transform
manager.

    cd leginon
    python update16.py

-   Add database configuration if you intend to use grid-inserting robot. The Robot2
    module uses the database to communicate to the robot. Applications that carries the name
    "Robot" requires this to be set. In general, using the same database as the general
    leginon database is fine.


    [robot2]
    db: dbemdata

## Install updated mrc module

php-mrc 1.5 uses fftw3. You may need to install that before installing the tool as a php
extension.

See php-mrc extenstion installation section in
Complete Installation Chapter.

## Install updated dbemtools

See dbemtools installation section in Complete
Installation Chapter.

## Reset installation status in projectdb

You can do this directly by mysql commands.

> mysql
projectdata

    > mysql projectdata -u usr_object
    mysql> drop table install;
    mysql> exit

Alternatively, you can use phpMyAdmin to achieve this by visiting the database, find the
table and click on drop.

## Install updated tools for project management

See projecttools installation section in
Complete Installation Chapter.

## Load default node settings for Leginon applications (optional)

Default settings are useful for new users of a new application. However, if you have
manually set these as administrator user in Leginon, loading these now will "overwrite" your
settings.

See admintools default loading section in
Complete Installation Chapter.
