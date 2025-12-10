By switching to svn package check out, you now need to install svn on Windows to get the
updated packages. Because numextension and libCV requires extra compiler, we have created
window installer for them for python 2.5 and made them available through <http://www.leginon.org/>

See Installation Troubleshooting and the [Leginon Forum](http://emg.nysbc.org/redmine/projects/leginon/boards/6) searching
for "install" if you run into problems.

## Packages required from NRAMM

Here are the packages you need to install with python installer

  SVN Package Name   Installed Python Package Name   Reason for update:
  ------------------ ------------------------------- -------------------------------------
  leginon            Leginon                         new features
  pyami              pyami                           clean up
  sinedon            sinedon                         new stuff
  pyScope            pyScope                         new instrument configuration
  ImageViewer        ImageViewer                     updated and required for tomography

Because numextension and libCV requires extra compiler, we have created window installer
for them for python 2.5 and made them available through <http://www.leginon.org/>

  Downloadfile Name                    Installed Python Package File   Reason for update:
  ------------------------------------ ------------------------------- --------------------
  NumExtension-1.2.0.win32-py2.5.exe   numextension.pyd                clean up
  libCV-0.2.win32-py2.5.exe            libCV.pyd                       bug fixes

## Uninstall your existing packages:

Although new installation overwrite the old in most cases, problem has been observed in
the past. Therefore, it is best to remove the old files before new installation.

Use "Add or Remove Programs" application in "Control Panel" to do this. Leginon related
packages are shown with prefix "Python 2.5"

If you didn't use Installer to install previously, the packages may not show up in the
Programs list. Simply remove the folder containing the old packages in this case.

## Download and install SVN client program:

By switching to svn package check out, you now need to install svn client on Windows to
get the updated packages. We recommand TortoiseSVN [http://tortoisesvn.tigris.org/](http://www.leginon.org/) .

## Check out SVN Source Files from the depository

Use your mouse to do the following

-   Create Leginon-1.6-ALL directory somewhere at your convenience
-   Change directory into Leginon-1.6-ALL
-   Right-click the mouse botton in this directory window and select Tortoise svn
    Checkout in the menu: ![](images/svnmenu.png)
-   Set up svn checkout window like this for each of the leginon package![](images/svnco.png)

## Install the packages you downloaded from NRAMM svn depository

-   Start a command line Window from Start Menu


-   Reinstall the package in each folder with commands such as
        cd Your_Download_Place\Leginon-1.6-ALL\leginon
        c:\python25\python.exe setup.py install

## Download the two Window Installer Files from Leginon website

<http://www.leginon.org/>

## Install individual packages

Excute the installer files and follow the instruction.
