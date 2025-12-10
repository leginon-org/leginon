    mkdir /sw/packages/SIMPLE
    cd /sw/packages/SIMPLE
    mkdir downloads
    cd downloads
    wget http://simple.stanford.edu/binaries/simple_linux_120521.tar.gz
    cd ..
    tar zxf downloads/simple_linux_120521.tar.gz
    cd simple_linux_120521
    ./simple_config.pl

type "local" when prompted.

This actually modifies the files in simple_linux_120521 to configure them with the correct path. This cannot later be modified by running ./simple_config.pl again on the same directory, so if you want to install somewhere other than /sw/packages/SIMPLE/simple_linux_120521, then you have to unpack a new copy from the tar.gz and run simple_config.pl once it is in the new location.

To set up your environment to use the executables in this new SIMPLE installation, you need both "apps" and "bin" subdirectory in your PATH. For example:

    export PATH=$PATH:/sw/packages/SIMPLE/simple_linux_120521/apps:/sw/packages/SIMPLE/simple_linux_120521/bin

WARNING: I notice that some commands in the bin directory are fairly generic names, so just be aware of this when adding this to PATH. For example, there is a command "align", so hopefully there is no other "align" command which conflicts with this.

[< Install EM Hole Finder](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_EM_Hole_Finder) | [Test Appion >](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Test_Appion)
