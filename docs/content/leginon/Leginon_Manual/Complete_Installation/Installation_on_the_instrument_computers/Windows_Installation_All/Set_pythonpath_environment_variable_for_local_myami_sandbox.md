## Set pythonpath environment variable for local myami sandbox

For an uninstall myami svn checkout, you can set PYTHONPATH environment variable to use it directly.

1.  Control Panel\All Control Panel Items\System> click on Advanced settings
2.  System Properties\Advanced> click on Environment Variables
3.  Either create a new variable for the current user, or do it system-widely.

PYTHONPATH should incldue both the base myamipath as well as leginon

For example, myami folder is at C:\Users\vagrant\Desktop\myami, then the python path should be set as follows:

    C:\Users\vagrant\Desktop\myami; C:\Users\vagrant\Desktop\myami\leginon


![](images/myami_pythonpath.png)
