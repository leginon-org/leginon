**Before you begin:**
Please note that Appion 2.2, Appion 2.2-redux and any earlier releases do not include any features that require EMAN2/SPARX to be installed. Appion 3.0, the development trunk and future releases will require this software.
This documentation assumes you are using CentOS 6 (written as of CentOS 6.5)
It is best to install EMAN2/SPARX from source to get MPI working on a cluster or to avoid conflicts with having two different versions of python on your system. Binaries of EMAN2/SPARX all come with their own python pre-installed.

## Install pre-requisite packages for EMAN2 compiling

### yum based packages

-   Make sure EPEL is install, if not go here: [Download additional Software (CentOS Specific)](/appion/Appion_Manual/Complete_Installation/Download_additional_Software_CentOS_Specific)
-   Use yum to install devel libraries:
        sudo yum install fftw-devel gsl-devel boost148-python numpy libjpeg-devel 
         PyQt4-devel cmake ipython hdf5-devel libtiff-devel libpng-devel boost148-devel 
         PyOpenGL db4-devel python-argparse openmpi-devel python-pip freeglut-devel ftgl-devel

## Download the source

1.  To download the source code go to the link:
    #* http://blake.bcm.edu/emanwiki/EMAN2
2.  Click on **"Main EMAN2 Download Page"**
3.  Click on **"Download EMAN 2"**, whichever is the latest release of EMAN.
4.  Scroll down to **Source** to download the **eman2.1beta3.source.tar.gz**

## Work with the source

1.  go to the directory with the source code
2.  extract the archive:
        tar zxvf eman2.12.source.tar.gz
3.  go into directory
        cd EMAN2/src/build
4.  start configure script:
        cmake ../eman2/

    
    #* Note: alternatively you can run `ccmake ../eman2/` and configure all the parameters
    #* I had to disable ftgl (fonts in OpenGL) to get 2.12 to compile.
    #* I had to manually set BOOST_LIBRARY=/usr/lib64/boost148/libboost_python.so
    #* I had to manually set BOOST_INCLUDE_PATH=/usr/include/boost148
    #* I had to manually set FREETYPE_INCLUDE_PATH=/usr/include/freetype2/
    #* I had to manually set FTGL_INCLUDE_PATH=/usr/include/FTGL/
    #* I had to manually set FTGL_LIBRARY=/usr/lib64/libftgl.so
        -- The C compiler identification is GNU 4.4.7
        -- The CXX compiler identification is GNU 4.4.7
        -- Check for working C compiler: /usr/bin/cc
        -- Check for working C compiler: /usr/bin/cc -- works
        -- Detecting C compiler ABI info
        -- Detecting C compiler ABI info - done
        -- Check for working CXX compiler: /usr/bin/c++
        -- Check for working CXX compiler: /usr/bin/c++ -- works
        -- Detecting CXX compiler ABI info
        -- Detecting CXX compiler ABI info - done
        -- Looking for fseek64
        -- Looking for fseek64 - not found
        -- Looking for fseeko
        -- Looking for fseeko - found
        -- Looking for ftell64
        -- Looking for ftell64 - not found
        -- Looking for ftello
        -- Looking for ftello - found
        -- Configuring done
        -- Generating done
        -- Build files have been written to: /emg/sw/EMAN2/src/build
5.  start compiling:
        make
6.  install to directory:
        sudo make install

## Set environmental variables

### bash

    sudo nano /etc/profile.d/eman2.sh

    export EMAN2DIR=/usr/local/EMAN2
    export PATH=${EMAN2DIR}/bin:${PATH}
    export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${EMAN2DIR}/lib
    export PYTHONPATH=${EMAN2DIR}/lib:${EMAN2DIR}/bin

### c shell

    sudo nano /etc/profile.d/eman2.csh

    setenv EMAN2DIR /usr/local/EMAN2
    setenv PATH ${EMAN2DIR}/bin:${PATH}
    setenv LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:${EMAN2DIR}/lib
    setenv PYTHONPATH ${EMAN2DIR}/lib:${EMAN2DIR}/bin

## Install MyMPI

-   First, add the openmpi module so that MyMPI can find it.
        module add openmpi-i386
        -or-
        module add openmpi-x86_64


-   Download source:
    From the main software page: http://ncmi.bcm.tmc.edu/ncmi/software/software_details?selected_software=counter_222 scroll to **MPI Support**.
    Click on **Download MPI Support**
    Click on **pydusa-1.15es.tgz**
-   Extract:
        tar zxvf pydusa-1.15es.tgz
-   go into directory
        cd pydusa-1.15es

    
     
    If you are on a 64bit machine, you may have problems with the code finding the numpy headers:
     
        nano configure

    
     
    find the line:
        elif test -d ${PY_PREFIX}/lib/python$PY_VERSION/site-packages/numpy/core/include; then
           PY_HEADER_NUMPY="-I${PY_PREFIX}/lib/python$PY_VERSION/site-packages/numpy/core/include"

    
    and replace it with:
     
        elif test -d ${PY_PREFIX}/lib64/python$PY_VERSION/site-packages/numpy/core/include; then
           PY_HEADER_NUMPY="-I${PY_PREFIX}/lib64/python$PY_VERSION/site-packages/numpy/core/include"
-   Configure:
        setenv MPIROOT /usr/lib64/openmpi
        setenv MPIINC /usr/include/openmpi-x86_64
        setenv MPILIB ${MPIROOT}/lib
        setenv MPIBIN ${MPIROOT}/bin
        ./configure

        export MPIROOT=/usr/lib64/openmpi
        export MPIINC=/usr/include/openmpi-x86_64
        export MPILIB=${MPIROOT}/lib
        export MPIBIN=${MPIROOT}/bin
        ./configure

    
    Please ensure mpicc was found. If it is not found, a version of MPI will be installed that may cause errors. Look for the following error and correct this issue before moving on:
        configure: error: Unable to find mpicc! mpicc location can be specified with --with-mpicc

    
     
-   compile the source:
        make
-   copy the mpi.so to site-packages with a different name:
        sudo mkdir /usr/lib64/python2.6/site-packages/mympi/
        sudo touch /usr/lib64/python2.6/site-packages/mympi/__init__.py
        sudo cp -v src/mpi.so /usr/lib64/python2.6/site-packages/mympi/mpi.so
-   create a wrapper around the wrapper:
        sudo nano /usr/lib64/python2.6/site-packages/mpi.py

        import ctypes
        mpi = ctypes.CDLL('libmpi.so.1', ctypes.RTLD_GLOBAL)
        from mympi.mpi import *

    
    This needs to be done to avoid the error:
        python: symbol lookup error: 
          /usr/lib64/openmpi/lib/openmpi/mca_paffinity_hwloc.so: 
            undefined symbol: mca_base_param_reg_int


-   test 1:
        python -c 'import mpi'
        python -c 'import sys; from mpi import mpi_init; mpi_init(len(sys.argv), sys.argv)'


-   test 2:
        sxisac.py start.hdf

    
    (Note: start.hdf does not need to exist, if it does not exist then it should exit with file not found)

## Test to see if code works

see http://blake.bcm.edu/emanwiki/EMAN2/FAQ/EMAN2_unittest

    cd EMAN2/test/rt
    ./rt.py

## Install MyMPI for MPI functions

see http://sparx-em.org/sparxwiki/MPI-installation
or https://www.nbcr.net/pub/wiki/index.php?title=MyMPI_Setup

This fixes this problem:

        from mpi import mpi_init
    ImportError: No module named mpi

This module was very difficult to get working, it seems to be a poorly supported python wrapper for MPI. So, what we are going to do is compile the module, rename it, and create a wrapper. So, essentially we are creating a wrapper around the wrapper. We can only hope they switch to [http://mpi4py.scipy.org/ mpi4py] in the future.

## Documentation

-   http://blake.bcm.edu/emanwiki/EMAN2/Install
-   http://blake.bcm.edu/emanwiki/EMAN2/FAQ/eman2BuildFAQ

[< Install EMAN 1](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_EMAN) | [Install SPIDER >](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_SPIDER)
