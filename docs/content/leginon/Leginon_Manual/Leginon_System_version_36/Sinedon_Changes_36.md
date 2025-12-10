We switch to use pymysql in 3.6 version. This merged in changes in myami-pymysql branch. pymysql has ping and reconnect built-in that keeps query from having time-out error.

Additional module is therefore needed:

    pip install PyMySQL==0.10.1

On the Windows PC, if you are using python 2.7.3 or other old python 2.7 versions that do not include pip, you will need to reinstall 2.7.16 or 2.7.18 that you will find under "Files" tab in this redmine site. All the other supporting packages are still usable but need to be installed into the new python.

See [Install pymysql on Windows PC](/leginon/Leginon_Manual/Leginon_System_version_pymysql/Install_pymysql_on_Windows_PC) for how to use the wheel file to do pip install since instruments are usually not connected to internet.

If you'd rather not to reinstall, you can continue using the old sinedon by copying all *.py files in the old subpackage to the new one.
