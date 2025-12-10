## Preparation

You will need these myami subpackages from the branch you want from our git repository.

  Name:         Purpose:
  ------------- ---------------------------------------------------
  leginon       modular TEM image acquisition
  pyami         general functions
  myami_test    test suite that is called before starting leginon
  sinedon       database interaction
  pyscope       microscope control and monitoring
  imageviewer   image viewing for tomography

## No internet access - copy from linux Leginon workstation the python files.

If your Windows computer has no access to internet, copy from your linux processing server the git clone of myami super package of the right branch for the installation which you used to upgrade there.

See [Acquiring NRAMM GIT Repository files](/leginon/Download_Appion_Files) for different examples and match the repository with what you do on the Linux side.

**OR**

## With internet access

### Clone the proper branch from git repository. You will want myami-3.4


### Start Git Bash Window

- Right Click at the folder where it will contain your clone and choose "Git Bash Here" to start the shell window.

- With Windows XP "Git Bash Here" does not appear with right-click. In this case, you can start git bash from **Start menu/Programs/Git/Git Bash** and move the folder created to where you want it to be.

### To checkout (called clone in git) the package from NRAMM: See [Acquiring NRAMM GIT Repository files](/leginon/Download_Appion_Files) for different examples and match the repository with what you do on the Linux side.


## Install

### Move the cloned folder according to your environment variable PYTHONPATH if you use that during the original installation.

**OR**

### Install to default python site-packages

-   Start a command line Window from Start Menu


-   Install the package in each folder (must starts with pyami)
        cd path_to\myami-VERSION\myami\pyami
        c:\python27\python.exe setup.py install

    
    Then continue with the other packages, replacing pyami with the package name. See the packages listed above for the complete list.

## Configure

[locate global config directory on Windows](/leginon/Locate_global_config_directory_on_Windows)

# FEI scopes

## fei.cfg

Compare yours_git_clone\pyscope\fei.cfg.template with your active fei.cfg There are additional configuration that you may want to add. Especially if you have Falcon 3.

# GatanK2Summit

Compare pyscope/dmsem.cfg.template with your active dmsem.cfg There are additional configuration that you may want to add.
