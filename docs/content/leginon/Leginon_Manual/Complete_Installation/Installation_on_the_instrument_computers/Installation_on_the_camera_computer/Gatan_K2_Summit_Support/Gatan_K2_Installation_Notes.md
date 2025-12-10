This is a preliminary document. Use at your own risk.

## Install the latest SerialEM DigitalMicrograph plugin: SEMCCD-GMS2-64.dll


Thanks to David Mastronarde for providing his DM plug-in using socket connection

## Note: If you have SerialEM installed on the same computer, you don't have to go through this.  The same Plugin can be used by both programs and share the same port

### Remove your older SEMCCDxxxx.dll in  C:\Program File\Gatan\Plugins if you had it from prevous leginon-only installtion

### Download and extract the files

 1. From your browser, go to [[ https://bio3d.colorado.edu/ftp/SerialEM/FrameAlignment/]]
 2. Choose Shrmemframe*..exe for your version of DM to download to your Gatan PC.
 3. Run the downloaded file and follow its instructions.

Add a new environment variable SERIALEMCCD_PORT if not exist already from SerialEM installation. Set the value to an unused port between 50000 and 60000 to avoid conflict with other programs. Avoid ports [used by Leginon](/leginon/Leginon_Manual/Complete_Installation/Network_Configuration/Ports_used_by_Leginon), especially not 55555.

Port 50000 or 50001 usually works.

![](images/SERIALEMCCD_environment.png)


## Install 64 bit versions of the usual Python stuff

The 64 bit Python installer failes to update the windows registry properly if installed for "all users". When installing other python packages, it will complain that it can't find python. To solve this, install Python only for the current user. Or search google for how to install for all users and then update the registry manually.

We have tested with:

-   Python 2.7.3: http://python.org/ftp/python/2.7.3/python-2.7.3.amd64.msi
-   PyWin32 extension: pywin32-218.win-amd64-py2.7.exe, available here: http://sourceforge.net/projects/pywin32/files/pywin32/Build%20218/
-   wxPython: http://downloads.sourceforge.net/wxpython/wxPython2.8-win64-unicode-2.8.12.1-py27.exe

Some of the other packages have no officially supported 64 bit versions, but they are easy to find with google. To save the trouble, I dumped some of them in our Files: http://emg.nysbc.org/redmine/projects/leginon/files including:

Tested:

-   MySQL-python-1.2.3.win-amd64-py2.7.exe
-   numextension-svn.win-amd64-py2.7.exe
-   numpy-MKL-1.6.2.win-amd64-py2.7.exe
-   PIL-fork-1.1.7.win-amd64-py2.7.exe
-   scipy-0.11.0.win-amd64-py2.7.exe
    (many of those originally came from http://www.lfd.uci.edu/~gohlke/pythonlibs/)

You do not need to install comarray or libcv.

## Install myami from svn trunk

Our usual routine lately is:

-   install Tortoise SVN client
-   check out myami trunk sandbox to wherever you want
-   Set PYTHONPATH to you myami sandbox, rather than installing each package to site-packages.

## Configure myami

-   create a folder: C:\Program Files\myami
-   copy the templates for config files into the new folder and rename them without the ".template"
    -   sinedon.cfg - edit with your DB settings
    -   leginon.cfg - edit with your leginon settings
    -   instruments.cfg - The camera modes are configured as separate cameras as follows. Note that Super Resolution should be double the size of Linear and Counting. Also note that zplane will be relative to any other cameras in your system. Anything below K2 should have a lower zplane.
        **In addition, to make the images acquired from the camera to have the [standard Leginon orientation](/leginon/Leginon_Manual/Instrument_Set-up/Leginon_image_orientation), the camera configuration in Digital Micrograph will need a rotation and flip (270 degree rotation and a flip around the vertical axis on our camera). Therefore, the height becomes longer than width**.
            [Gatan K2 Linear]
            class: dmsem.GatanK2Linear
            zplane: 50
            width: 3710
            height: 3838

            [Gatan K2 Counting]
            class: dmsem.GatanK2Counting
            zplane: 50
            width: 3710
            height: 3838

            [Gatan K2 Super]
            class: dmsem.GatanK2Super
            zplane: 50
            width: 7420
            height: 7676

## Try it out

Need to start DigitalMicrograph first

Test pyscopy without leginon from python command line:

    import pyscope.dmsem
    k = pyscope.dmsem.GatanK2Counting()
    k.setExposureTime(200)
    k.getImage()

Then try Leginon.

[Using Gatan K2 Summit in Leginon](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Gatan_K2_Summit_Support/Using_Gatan_K2_Summit_in_Leginon)
