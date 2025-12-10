myami-pymysql is created to use pymysql instead of python-MySQL supporting package. The change is required for python 2 to 3 conversion in the work. It
also handles better situation where mysql connection is dropped by the database server.

This branch is maintained at approximately the same revision as myami-beta. This is updated after NYSBC tested myami-beta after any new feature or bug fixes are added.

# Use of this branch on Windows PC has not yet passed our testing. [install pymysql on Windows PC](/leginon/Leginon_Manual/Leginon_System_version_pymysql/Install_pymysql_on_Windows_PC) Please install myami-beta on it while using myami-pymysql branch on Unix system.

## pymysql installation on Unix system

Best to use pip to match your python version. See Issue #7751 for more details.

    pip install pymysql
