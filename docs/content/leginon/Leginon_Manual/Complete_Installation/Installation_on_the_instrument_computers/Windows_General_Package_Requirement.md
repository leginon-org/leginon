You should generally be able to use the most recent versions of these packages that are available from their respective web sites. Just be sure to always get the version that is compatible with Python 2.7. However, you must use the exact version for numpy. If you are having trouble with the most recent version, try to use the specific versions we include in http://emg.nysbc.org/redmine/projects/leginon/files



------------------------------------------------------------------------

Program package web site local copy of win32 installer local copy of amd64 installer
Python > 2.7.10 <http://www.python.org> python-2.7.16.msi python-2.7.18.amd64.msi
wxPython 2.8 or newer <http://www.wxpython.org> wxPython2.8-win32-unicode-2.8.12.1-py27.exe wxPython2.8-win64-unicode-2.8.12.1-py27.exe
MySQL Python client 1.2 or newer <http://sourceforge.net/projects/mysql-python> MySQL-python-1.2.4b4.win32-py2.7.exe MySQL-python-1.2.3.win-amd64-py2.7.exe
Python Imaging Library (PIL) 1.1.4 or newer <http://www.pythonware.com/products/pil/> PIL-1.1.7.win32-py2.7.exe PIL-fork-1.1.7.win-amd64-py2.7.exe
NumPy (use only from our file to match compiled numextension numpy-1.7.0-win32-python2.7.exe numpy-MKL-1.6.2.win-amd64-py2.7.exe
SciPy 0.5.1 or newer <http://www.scipy.org> scipy-0.11.0-win32-superpack-python2.7.exe scipy-0.11.0.win-amd64-py2.7.exe
------------------------------------------------------------------- ------------------------------------------------------------------------------------ ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Use pyMySQL for leginon 3.6 and above instead of MySQL Python client for both win32 and 64.
|pyMySQL 0.10.1 (not higher)|https://pypi.org/project/PyMySQL/|pyMySQL-0.10.1-py2.py3-none-any.whl


## (trunk, beta, 3.3 and up) GIT client used for check out from our repository


We have switched to git revision control recently. If you want to install the newest changes, you need to use the files from git repository.

You can clone our repository with

Name: Download site:
------------------------- -------------------------------------------------------
git for Windows <https://git-for-windows.github.io>

- During the installation, select "Checkout as-is, commit as-is" option at the step regarding automated translation of CRLF and LF line endings if you are a developer and may commit changes.
- Default is fine with the rest of the options.


# Packages from NRAMM

Most of the subpackages from NRAMM are obtained through our repository. You have two option depending on your situation

1.  [Clone from git repository (newer version)](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Windows_General_Package_Requirement#Cloning-myami-git-repository)
2.  Copy your git clone or svn checkout from your linux box if you do not have internet access on instrument PC.

## Cloning myami git repository

We recommend using git bash to do so which gives most freedom in configuration and so that you can use unix syntax.
[git for windows cloning](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Windows_General_Package_Requirement/Git_for_windows_cloning)

-   Right Click at the folder where it will contain your clone and choose "Git Bash Here" to start the shell window.


-   With Windows XP "Git Bash Here" does not appear with right-click. In this case, you can start git bash from **Start menu/Programs/Git/Git Bash** and move the folder created to where you want it to be.

### To checkout (called clone in git) the package from NRAMM:

See [Acquiring NRAMM Repository files](/leginon/Download_Appion_Files) for different examples and match the repository with what you do on the Linux side.

## numextension windows installer

Because numextension and would require extra compilers if you build them yourself, we have created Windows installers for them for python 2.7 and made them available at /redmine/projects/leginon/files.

## These are the current Leginon python 2.7 compiled packages you should install by opening them on Windows.


Package win32 amd64
--------------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
numextension numextension-svn.win32-py2.7-numpy1.7.0.exe numextension-svn.win-amd64-py2.7-numpy1.6.2.exe



[Windows Installation That apply to all instruments >](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Windows_Installation_All)
