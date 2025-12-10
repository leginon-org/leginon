## Install documentation at wadsworth.org

The Wadsworth Institute provides [detailed documentation](http://www.wadsworth.org/spider_doc/spider/docs/spider-inst-linux.html) on how to install SPIDER on various systems. Below we cover *our way* to get it working on your system.

## Download SPIDER binary [from wadsworth.org](http://www.wadsworth.org/spider_doc/spider/docs/spi-register.html) (1 GiB)

> Most of our SPIDER scripts were originally designed around SPIDER v14 and v15, but we are diligently working toward compatibility with SPIDER v18. That said you are probably best off using the newest version of SPIDER (v21.13 as of February 2014) and then reporting any bugs to us.

## Extract the archive

    tar -zxvf spiderweb.21.13.tar.gz

> The archive will create 3 folders: spider, spire, and web. At this time only the **spider** program is used within Appion, you can safely ignore web and spire.

## Install SPIDER

-   Copy the spider folder to global directory:
        sudo mv -v spider /usr/local/


-   Next, you need to determine which version of the spider binary you need to use on your system.
        cd /usr/local/spider/bin
        ls spider*
          spider_linux           spider_linux_mp_intel64  spider_linux_mp_opt64  spider_osx_64_pgi
          spider_linux_mp_intel  spider_linux_mpi_opt64   spider_osx_32_pgi


-   From the wadsworth.org site:
    |*. binary file |*. system information |
    | spider_linux | AMD/Intel 32 (single processor) |
    | spider_linux_mp_intel | AMD/Intel 32 (multiple processors) |
    | spider_linux_mp_opt64 | AMD Opteron 64 (multiple processors) |
    | spider_linux_mp_intel64 | Intel xeon 64 (multiple processors) |
    | spider_linux_mpi_opt64 | AMD Opteron 64 (for MPI use) |
    | spider_osx_32_pgi | Intel Apple 32 bit (multiple processors) |
    | spider_osx_64_pgi | Intel Apple 64 bit (multiple processors) |


-   Additionally you may run the UNIX file command on an individual program to determine its type
        file spider_linux_mp_intel64
          spider_linux_mp_intel64: ELF 64-bit LSB executable, AMD x86-64, version 1 (SYSV), for GNU/Linux 2.6.4, 
          statically linked, for GNU/Linux 2.6.4, not stripped


-   If you are unsure, use:
    -   `spider_linux_mp_intel` for 32bit Intel/AMD systems
    -   `spider_linux_mp_opt64` for 64bit Intel/AMD systems


-   After you determine which spider to use create a link to that file in /usr/local/bin:
        sudo ln -sv /usr/local/spider/bin/spider_xxxxx /usr/local/bin/spider

## Set environmental variables

### For `BASH`, create an spider.sh and add the following lines:

    export SPIDERDIR=/usr/local/spider
    export SPMAN_DIR=${SPIDERDIR}/man/
    export SPPROC_DIR=${SPIDERDIR}/proc/
    export SPBIN_DIR=${SPIDERDIR}/bin/
    export PATH=$PATH:${SPIDERDIR}/bin

### For `C` shell, create an spider.csh and add the following lines:

    setenv SPIDERDIR /usr/local/spider
    setenv SPMAN_DIR ${SPIDERDIR}/man/
    setenv SPPROC_DIR ${SPIDERDIR}/proc/
    setenv SPBIN_DIR ${SPIDERDIR}/bin/
    setenv PATH $PATH:${SPIDERDIR}/bin

### And then add it to the global /etc/profile.d/ folder

    sudo cp -v spider.sh /etc/profile.d/spider.sh
    sudo chmod 755 /etc/profile.d/spider.sh

    -or-

    sudo cp -v spider.csh /etc/profile.d/spider.csh
    sudo chmod 755 /etc/profile.d/spider.csh

> You may need to log out and log back in for these changes to take place.

## Test SPIDER

-   Execute the program:
    -   input:
            spider bat/spi
    -   output:

             __`O O'__/        SPIDER  --  COPYRIGHT
             ,__xXXXx___        HEALTH RESEARCH INC., ALBANY, NY.
              __xXXXx__
             /  /xxx\  \        VERSION:  UNIX  18.10 ISSUED: 03/23/2010
               /     \          DATE:     13-MAY-2010    AT  09:32:42



             Results file: results.bat.0
             Running: spider

             .OPERATION:
    -   input:
            EN D
    -   output:
             **** SPIDER NORMAL STOP ****

[< Install EMAN](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_EMAN) | [Install Xmipp >](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_Xmipp)
