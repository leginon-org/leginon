## Preparation

You will need these myami subpackages updated.

  Name:        Purpose:
  ------------ ---------------------------------------------------
  leginon      modular TEM image acquisition
  pyami        general functions
  myami_test   test suite that is called before starting leginon
  sinedon      database interaction
  pyscope      microscope control and monitoring

## No internet access - copy from linux Leginon workstation the python files.

If your Windows computer has no access to internet, copy from your linux processing server the git clone of myami super package of the right branch for the installation which you used to upgrade there.

See [Acquiring NRAMM GIT Repository files](/leginon/Download_Appion_Files) for different examples and match the repository with what you do on the Linux side.

**OR**

## With internet access

### Clone the proper branch from git repository. You will want myami-3.5


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

Compare yours_git_clone\pyscope\fei.cfg.template with your active fei.cfg. Especially if you plan to use new featured instruments or have had a TEMServer upgrade to recent versions.

### If you set for your Talos column

    FORCE_NORMALIZE_ALL_LENS_AFTER_MAG_SETTING = True

please change it to use

    FORCE_NORMALIZE_ALL_AFTER_SETTING = True

This is more generalized and produces better results. See Issue #7076 for more details.

# GatanK2Summit or K3

Compare pyscope/dmsem.cfg.template with your active dmsem.cfg There are additional configuration that you may want to add.

-   Check if you need to specify ACQUISITION_SHUTTER_NUMBER differently (See Issue #7834)

# New Features

Follow [PyScope Changes 35](/leginon/Leginon_Manual/PyScope_Changes_35) on the installation and setup of the specific feature you want to activate.
