## Install win32 version of python subpackages

Use the 32-bit Windows files (those marked as win32 and certainly not the ones says 64) in http://emg.nysbc.org/redmine/projects/leginon/files for these.

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


## Required scripting from FEI

  ----------------------------------- --------------------------------------------------------------- ---------------------------------------------------------------------------------
  TEM Scripting or Tecnai Scripting   Request this when purchasing the microscope                     Required
  TomMoniker Scripting                Should come with TEM Scripting                                  Required
  Low Dose Server Library             Should come with the microscope if low dose kit was purchased   Required only if you want to use low dose kit with Leginon's Manual Application
  ----------------------------------- --------------------------------------------------------------- ---------------------------------------------------------------------------------

### Run checkcom.py

-   From a command line window:
        cd C:\python27\Lib\site-packages\pyscope
        C:\python27\python.exe checkcom.py


-   The output should at least find typelib for
        TEM Scripting

    
    and
        TOM Moniker

If you have Low Dose Kit

    Tecnai Low Dose Kit

You will only find Tecnai Exposure Adaptor (Scripting for film exposure) if you ask FEI for it.

## instruments.cfg

cs is **constant for sperical abberation**

For Tecnai series:

    [TEM]
    class: fei.Tecnai
    cs: 2.0e-3

For Halo (Titan column with tecnai compustage):

    [TEM]
    class: fei.Halo
    cs: 2.7e-3

For Krios (different compustage)

    [TEM]
    class: fei.Krios
    cs: 2.7e-3

For Krios EF mode, treated as a separate instrument. i.e. add

    [TEM]
    class: fei.EFKrios
    cs: 2.7e-3

## Setup fei.cfg

> **Note:** See [setup fei.cfg](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_microscope_computer_30/FEI_TecnaiTitan_installation_specifics/Setup_feicfg)

## Testing with pyscope

For Tecnai series In python command

    from pyscope import fei
    t = fei.Tecnai()
    t.getMagnification()

For Krios

    from pyscope import fei
    t = fei.Krios()
    t.getMagnification()

For Krios with EF-TEM mode, activate EF-TEM mode on the scope, and then do the following

    from pyscope import fei
    t = fei.EFKrios()
    t.getMagnification()

For Halo

    from pyscope import fei
    t = fei.Halo()
    t.getMagnification()

You should get the current magnification at the microscope when the main viewing screen is up

## Trouble Shooting

[unable to initializ Tecnai interface error](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_microscope_computer_30/FEI_TecnaiTitan_installation_specifics/Unable_to_initializ_Tecnai_interface_error)

## Programs to open before Leginon Client: None
