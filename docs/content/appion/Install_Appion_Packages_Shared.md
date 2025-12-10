    cd /path/to/myami-VERSION/myami
    sudo ./pysetup.sh install

That will install each package, and report any failures. To determine the cause of failure, see the generated log file "pysetup.log".

> **Note:** See external reference `Leginon:packages installed by pysetup.sh`

### alternatively, install a specific package in turn

If necessary, you can enter a specific package directory and run the python setup command manually. For example, if pyami failed to install, you can try again like this:

    cd pyami
    sudo python setup.py install

### python-site-package-path: where the installed python packages went:

Python installer put the packages you installed into its site-packages directory. This enables all users on the same computer to access them. The easiest way to discover where your installed package is loaded from by python is to load a module from the package using interactive python command lines like this:

Start the python command line from shell:


python


Import a module from the package. Let's try pyami here. All packages installed through the above setup.py script should go to the same place.
At the python prompt (python>) type:

    import pyami

If the module is loaded successfully, call the module attribute *path* (two underscrolls before "path" and two underscrolls after) will return the location of the module it is loaded from

    pyami.__path__
    ['/usr/lib/python2.6/site-packages/pyami']

In this case, /usr/lib/python2.6/site-packages/ is your python-site-package-path. If you go to that directory, you will find all the packages you just installed.

Save this value as an environment variable for use later, for bash:

    export PYTHONSITEPKG='/usr/lib/python2.6/site-packages'


or C shell

    setenv PYTHONSITEPKG '/usr/lib/python2.6/site-packages'
