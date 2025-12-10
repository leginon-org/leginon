The "EM Hole Finder" package is used for the Auto-masking feature of Appion, available with version 3.0. It automatically detects carbon edges in micrographs and creates masks for the images to hide the carbon portions. These masks can then be used to exclude particles in those regions from particle stacks.

## Download em_hole_finder package

The package is available at

https://github.com/hbradlow/em_hole_finder

## Installation Instructions for CentOS 6

em_hole_finder uses a version of numpy which is not compatible with the rest of Appion.
When the em_hole_finder program is called from Appion, it must first run an activation script to set up an appropriate environment for running em_hole_finder. The instructions below include installing a virtual environment package. Packages installed after sourcing the activate script will be used only for em_hole_finder while running within Appion.

    yum install git python-virtualenv libjpeg-devel -y
    easy_install pip
    cd /opt
    git clone https://github.com/hbradlow/em_hole_finder
    cd em_hole_finder
    virtualenv env
    source env/bin/activate
    pip install numpy
    pip install Cython
    pip install PIL
    pip install scipy
    pip install scikit-image
    pip install ipython
    pip install wsgiref

#### Make find_mask.py executable

    chmod +x find_mask.py

## Set environment variables

To call em_hole_finder from Appion, the installed package directory (em_hole_finder) needs to be in the user's PATH variable. Make sure, *which find_mask.py* returns the correct path. For instance:

    $ which find_mask.py
    /opt/em_hole_finder/find_mask.py


Also, you need to set an environment variable "HOLE_FIND_ACTIVATE" to the path to the activate script. An example of the path is "/opt/em_hole_finder/env/bin" where a script called activate is located in the bin directory.

[< Install Protomo](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_Protomo) | [Install SIMPLE >](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_SIMPLE)
