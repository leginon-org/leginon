  Name:                      Download site:                          SuSE rpm name   Debian 8 package name
  -------------------------- --------------------------------------- --------------- -----------------------
  joblib 0.8.3-r1 or newer   <https://pypi.python.org/pypi/joblib>   python-joblib   python-joblib

joblib can be installed with the command

    easy_install joblib==0.10.3

-   The specific version is compatible with python 2.6 on CentOS 6
-   If python 2.7 is used, the version does not need to be specified.

If that does not work because the version is not found. Try this on CentOS6

    yum install python-pip
    pip install joblib==0.10.3
