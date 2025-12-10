## Install win32 version of python subpackages

Because all interaction with the scope uses COM interface that is only accessible through 32-bit architecture, python running Leginon component is the 32-bit version. Use the 32-bit Windows files (those marked as win32 and certainly not the ones says 64) in http://emg.nysbc.org/redmine/projects/leginon/files for these.

Here is the full list



------------------------------------------------------------------------

Program package web site local copy of win32 installer
Python 2.7.16 https://www.python.org python-2.7.16.msi
wxPython 2.5.2.8 or newer <https://www.wxpython.org> wxPython2.8-win32-unicode-2.8.12.1-py27.exe
Python Imaging Library (PIL) 1.1.4 or newer <http://www.pythonware.com/products/pil/> PIL-1.1.7.win32-py2.7.exe
NumPy (use only from our file to match compiled numextension numpy-1.7.0-win32-python2.7.exe
SciPy 0.5.1 or newer <http://www.scipy.org> scipy-0.11.0-win32-superpack-python2.7.exe
------------------------------------------------------------------- ------------------------------------------------------------------------------------ ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Leginon 3.5 or before
|MySQL Python client 1.2 or newer| [http://sourceforge.net/projects/mysql-python](http://sourceforge.net/projects/mysql-python|MySQL-python-1.2.4b4.win32-py2.7.exe)

Leginon 3.6 and up
|pyMySQL 0.10.1 (not higher)|https://pypi.org/project/PyMySQL/|pyMySQL-0.10.1-py2.py3-none-any.whl




------------------------------------------------------------------------

Program package web site local copy of win32 installer
comtypes 0.6.2 [http://sourceforge.net/projects/comtypes](http://sourceforge.net/projects/comtypes/files/comtypes/0.6.2/comtypes-0.6.2.win32.exe") comtypes-0.6.2.win32.exe
------------------------ ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -------------------------------------------------------------------------------------------------------------------------------------


## Important: Install Python under a custom named folder

**If your Talos/Arctica has a 64-bit Python pre-installed unde default python location C:\Python27, we need to name our installation with another name, such as C:\Python27-win32.**
This is set during python installation.

The rest of the installation is similar to other FEI systems.

## instruments.cfg

cs is **constant for sperical abberation**

For Talos series:

    [TEM]
    class: fei.Talos
    cs: 2.7e-3

For Arctica series:

    [TEM]
    class: fei.Arctica
    cs: 2.7e-3

For Glacios series:

    [TEM]
    class: fei.Glacios
    cs: 2.7e-3

## Testing with pyscope

In python command

For Talos:

    from pyscope import fei
    t = fei.Talos()
    t.getMagnification()

For Arctica:

    from pyscope import fei
    t = fei.Arctica()
    t.getMagnification()

For Glacios:

    from pyscope import fei
    t = fei.Glacios()
    t.getMagnification()

## Trouble Shooting

[unable to initializ Tecnai interface error](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_microscope_computer_30/FEI_TecnaiTitan_installation_specifics/Unable_to_initializ_Tecnai_interface_error)

## Programs to open before Leginon Client: None
