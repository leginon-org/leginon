## Install documentation at Xmipp

Biocomputing Unit at the Spanish National Center of Biotechnology (CNB-CSIC) provides [detailed documentation](http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/InstallingTheSoftware) on how to install Xmipp on various systems. Below we cover *our way* to get it working on your system.

## Install supporting packages

  Name:           Download site:   CentOS package name   Fedora package name   SuSE rpm name
  --------------- ---------------- --------------------- --------------------- ---------------
  gcc-c                            gcc-c                                       
  openmpi-devel                    openmpi-devel                               
  libtiff-devel                    libtiff-devel                               
  libjpeg-devel                    libjpeg-devel         libjpeg-turbo-devel   
  zlib-devel                       zlib-devel                                  

## Install Xmipp from source

We recommend installing Xmipp from source to properly use the openmpi libraries that allows you to run on multiple processors

### Download source code

-   Download the v2.4 source code from http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/HowToInstall
-   Unzip the source code:
        tar zxvf Xmipp-2.4-src.tar.gz

Alternatively, you may download from the svn repo:

    svn co http://newxmipp.svn.sourceforge.net/svnroot/newxmipp/tags/release-2.4/xmipp/ Xmipp-2.4-src

As of Nov 2013, this was required to compile the 2.4 source code.

### Prepare Xmipp make files

-   Go into Xmipp source directory
-   Find openmpi directory
        locate libmpi.so
        /usr/lib/openmpi/1.2.7-gcc/lib/libmpi.so

**Note:** If you can not find the openmpi directory, make sure you have installed the openmpi package. The installation on CentOS using yum is: yum -y install openmpi-devel.

### Compile the source code

-   Setup Xmipp to use openmpi by the following command. Be sure to modify the path in the second command as needed. For example, on a 32 bit machine using 1.4-gcc the command is:
    export PATH=$PATH:/usr/lib64/openmpi/bin

#### CentOS 5

    export PATH=$PATH:/usr/lib64/openmpi/1.3.2-gcc/bin
    ./scons.configure 
     MPI_LIBDIR=/usr/lib/openmpi/1.2.7-gcc/lib/ 
     MPI_INCLUDE=/usr/lib/openmpi/1.2.7-gcc/include/ 
     MPI_LIB=mpi

#### CentOS 6

**Note:** If you are installing Xmipp on x86_64 CentOS 6, you can use the following commands instead.

    export PATH=/usr/lib64/openmpi/bin:$PATH
    ./scons.configure 
     MPI_LIBDIR=/lib/usr/lib64/openmpi/lib 
     MPI_INCLUDE=/lib/usr/lib64/openmpi/include 
     MPI_LIB=mpi

-   Look for the following line in the output:


    * Checking for MPI ... yes

-   Now compile the source code


    ./scons.compile

-   Move the main source code directory to global location, like `/usr/local`


    sudo mv -v Xmipp-2.4-src /usr/local/Xmipp

### Setup environmental variables

-   For bash, edit xmipp.sh:
        export XMIPPDIR=/usr/local/Xmipp
        export PATH=${XMIPPDIR}/bin:${PATH}
        export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${XMIPPDIR}/lib
-   For C shell, edit xmipp.csh:
        setenv XMIPPDIR /usr/local/Xmipp
        setenv PATH ${XMIPPDIR}/bin:${PATH}
        setenv LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:${XMIPPDIR}/lib
-   Copy to /etc/profile.d
        sudo cp -v xmipp.sh /etc/profile.d/
        sudo chmod 755 /etc/profile.d/xmipp.sh

        - or -

        sudo cp -v xmipp.csh /etc/profile.d/
        sudo chmod 755 /etc/profile.d/xmipp.csh

> You may need to log out and log back in for these changes to take place, or source the environment script:

     source /etc/profile.d/xmipp.sh

## Test Xmipp

Test Xmipp by running ml_align2d program

    xmipp_ml_align2d -h


This result should appear

    2104:Argument -i not found or invalid argument
    File: libraries/data/args.cpp line: 502
    Usage:  ml_align2d [options] 
       -i <selfile>                : Selfile with input images 
       -nref <int>                 : Number of references to generate automatically (recommended)
       OR -ref <selfile/image>         OR selfile with initial references/single reference image 
     [ -o <rootname> ]             : Output rootname (default = "ml2d")
     [ -mirror ]                   : Also check mirror image of each reference 
     [ -fast ]                     : Use pre-centered images to pre-calculate significant orientations
     [ -thr <N=1> ]                : Use N parallel threads 
     [ -more_options ]             : Show all possible input parameters 

[< Install SPIDER](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_SPIDER) | [Install UCSF Chimera >](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_UCSF_Chimera)
