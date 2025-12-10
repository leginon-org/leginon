  --------------------------------------------- -------------------------------------------------------- ------------------------------------------------------------------------------------------------------------------------------- -------------------------------------------------------------------------------------------------------------------------------
  Program                                       package web site                                         local copy of win32 installer                                                                                                   local copy of amd64 installer
  Python > 2.7.10                              <http://www.python.org>                                  python-2.7.16.msi                                                      python-2.7.18.amd64.msi
  wxPython 2.8 or newer                         <http://www.wxpython.org>                                wxPython2.8-win32-unicode-2.8.12.1-py27.exe   wxPython2.8-win64-unicode-2.8.12.1-py27.exe
  MySQL Python client 1.2 or newer              <http://sourceforge.net/projects/mysql-python>           MySQL-python-1.2.4b4.win32-py2.7.exe                 MySQL-python-1.2.3.win-amd64-py2.7.exe
  Python Imaging Library (PIL) 1.1.4 or newer   <http://www.pythonware.com/products/pil/>                PIL-1.1.7.win32-py2.7.exe                                       PIL-fork-1.1.7.win-amd64-py2.7.exe
  NumPy                                         (use only from our file to match compiled numextension   numpy-1.7.0-win32-python2.7.exe                 numpy-MKL-1.6.2.win-amd64-py2.7.exe
  SciPy 0.5.1 or newer                          <http://www.scipy.org>                                   scipy-0.11.0-win32-superpack-python2.7.exe     scipy-0.11.0.win-amd64-py2.7.exe
  --------------------------------------------- -------------------------------------------------------- ------------------------------------------------------------------------------------------------------------------------------- -------------------------------------------------------------------------------------------------------------------------------

Use pyMySQL for leginon 3.6 and above instead of MySQL Python client for both win32 and 64.
|pyMySQL 0.10.1 (not higher)|https://pypi.org/project/PyMySQL/|pyMySQL-0.10.1-py2.py3-none-any.whl
