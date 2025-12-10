## Preparation

You will need these myami subpackages from the branch you want from our git repository.

  Name:         Purpose:
  ------------- -----------------------------------
  leginon       modular TEM image acquisition
  pyami         general functions
  sinedon       database interaction
  pyscope       microscope control and monitoring
  imageviewer   image viewing for tomography

## No internet access - copy from linux Leginon workstation the python files.

If your Windows computer has no access to internet, copy from your linux processing server the git clone of myami super package of the right branch for the installation which you used to upgrade there.

See [Acquiring NRAMM GIT Repository files](/leginon/Download_Appion_Files) for different examples and match the repository with what you do on the Linux side.

**OR**

## With internet access

### Install Git-for-Windows


We have switched to git revision control recently. If you want to install the newest changes, you need to use the files from git repository.

You can clone our repository with

Name: Download site:
------------------------- -------------------------------------------------------
git for Windows <https://git-for-windows.github.io>

- During the installation, select "Checkout as-is, commit as-is" option at the step regarding automated translation of CRLF and LF line endings if you are a developer and may commit changes.
- Default is fine with the rest of the options.


### Clone the proper branch from git repository


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

# FEI scopes

tecnai.py is now renamed to fei.py and requires a configuration file.

## [change instruments.cfg](/leginon/Leginon_Manual/How_to_Update_from_v32_Instrument_Windows_Computer/Tecnai_to_fei_Instrumentscfg_change)

## [setup fei.cfg](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_microscope_computer_30/FEI_TecnaiTitan_installation_specifics/Setup_feicfg)

# GatanK2Summit

Compare pyscope/dmsem.cfg.template with your active dmsem.cfg There are additional configuration that you may want to add.
