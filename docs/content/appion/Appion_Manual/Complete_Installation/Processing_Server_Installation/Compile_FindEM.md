## Install supporting packages:

  Name:                   Download site:   yum package name        SuSE rpm name
  ----------------------- ---------------- ----------------------- ---------------
  compat-gcc-34-g77                        compat-gcc-34-g77       
  gcc-gfortran                             gcc-gfortran            
  compat-libgfortran-41                    compat-libgfortran-41   

CenOS7

  Name:                   Download site:   yum package name
  ----------------------- ---------------- -----------------------
  compat-libf2c-34                         compat-libf2c-34
  compat-libgfortran-41                    compat-libgfortran-41

## Test FindEM binary

Both 32 and 64 bit findem binaries are already available in the myami/appion/bin directory.
Test it by changing directories to myami/appion/bin and type the following commands:

    ./findem64.exe         (64 bit version)

    or

    ./findem32.exe         (32 bit version)


If it does not crash you are good.

## Install FindEM from source

If the binary included with Appion does not work, or you wish to compile it yourself follow the instructions to [install FindEM from source](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Compile_FindEM/Install_FindEM_from_source).

[< Install Grigorieff lab software](/appion/Install_Grigorieff_lab_software) | [Install Ace2 >](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_Ace2)
