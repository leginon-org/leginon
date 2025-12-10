## Pre-install

-   The python radermacher module requires using openmp libraries. This allows for it to use more than one processor on a single machine and therefore runs faster. To install the open source openMP software on CentOS type:


    sudo yum install libgomp

## Build and install

-   Goto radermacher module folder:


    cd myami/modules/radermacher

-   compile the libraries and binary


    $ python ./setup.py build

-   install module globally


    $ sudo python ./setup.py install

## Quick test to see if installed properly

-   test installed module


    $ python

    >>> import radermacher
    >>> <Ctrl-D>

[< Compile Ace2](/appion/Compile_Ace2) | [Install Xmipp >](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_Xmipp)
