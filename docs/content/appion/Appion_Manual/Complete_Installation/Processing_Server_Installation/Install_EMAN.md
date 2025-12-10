EMAN1 is a fundamental package used in Appion for general file conversion and image filtering.

## Download latest EMAN1 (not EMAN2) binaries (currently version 1.9):

1.  Go to the [EMAN webpage](http://blake.bcm.tmc.edu/eman/)
2.  Click on `(download)` next to `EMAN1`
3.  Scroll to Download 1.9
    #* Note: For CentOS 6, you should download the latest nightly snapshot. (eman.daily.linuxcluster.tar.gz)
4.  Click on `Download 1.9` link
5.  Select the appropriate package
    #* we recommend using the `cluster` version of EMAN1
    #* x86 for 32bit and x86_64 for 64bit machines
    #* In this case, we would download the "eman-linux-x86_64-cluster-1.9.tar.gz"

-   We have tgz files under **Files** tag of this website

## Install EMAN

1.  Go to download directory and unzip the tar file:
        tar -zxvf eman-linux-x86_64-cluster-1.9.tar.gz
2.  Move the unzipped folder to a global location
        sudo mv -v EMAN /usr/local/
3.  Run the EMAN installer, it sets up the EMAN python module (must be run from the EMAN directory)
        cd /usr/local/EMAN/
        ./eman-installer

## Set enivromental variables

#* For `BASH`, create an eman.sh and add the following lines:

    export EMANDIR=/usr/local/EMAN
    export PATH=${EMANDIR}/bin:${PATH}
    export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${EMANDIR}/lib
    export PYTHONPATH=${EMANDIR}/lib


#* For `C` shell, create an eman.csh and add the following lines:

    setenv EMANDIR /usr/local/EMAN
    setenv PATH ${EMANDIR}/bin:${PATH}
    setenv LD_LIBRARY_PATH ${EMANDIR}/lib
    setenv PYTHONPATH ${EMANDIR}/lib


#* And then add it to the global /etc/profile.d/ folder

    sudo cp -v eman.sh /etc/profile.d/eman.sh
    sudo chmod 755 /etc/profile.d/eman.sh

    - or -

    sudo cp -v eman.csh /etc/profile.d/eman.csh
    sudo chmod 755 /etc/profile.d/eman.csh

> You may need to log out and log back in for these changes to take place.

## Test EMAN install

Run `proc2d`

    proc2d help

Should popup a window displaying help for proc2d

[< Install dosefgpu driftcorr](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_dosefgpu_driftcorr) | [Install EMAN2 >](/appion/Install_EMAN2)
