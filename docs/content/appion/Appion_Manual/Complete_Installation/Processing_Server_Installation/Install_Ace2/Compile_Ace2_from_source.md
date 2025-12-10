## Install supporting packages

  Name:         Download site:   yum package name   SuSE rpm name
  ------------- ---------------- ------------------ ---------------
  gcc-objc                       gcc-objc           
  fftw3-devel                    fftw3-devel        
  gsl-devel                      gsl-devel          

## Compile Ace 2 from source with FFTW 3.2 or later

It is recommended that you use FFTW version 3.2 or later, because there are optimizations in FFTW 3.2 that make Ace2 run significantly faster than FFTW 3.1 (which is distributed with CentOS). But **this is much harder**. You will need to install FFTW 3.2 from source code and then add the -DFFTW32 flag to the CFLAGS line in the Makefile

## Compile Ace 2 from source with FFTW 3.1

-   Goto myami/programs/ace2 folder
        cd programs/ace2
-   Run the makefile
        make
-   Test to make sure the programs run:
        ./ace2.exe -h
        ./ace2correct.exe -h
-   Copy the binary files to /usr/local/bin folder
        sudo cp -v ace2.exe ace2correct.exe /usr/local/bin/

    

[Install Ace2 ^](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_Ace2)
