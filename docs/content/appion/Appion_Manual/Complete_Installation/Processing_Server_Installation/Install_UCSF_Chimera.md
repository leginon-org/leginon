## Versions of UCSF Chimera:

Chimera has two pages and five sections for downloading the UCSF Chimera program:

-   [The main download page](http://www.cgl.ucsf.edu/chimera/download.html)
    -   Current production releases
    -   Daily builds
    -   Snapshot releases
    -   Unsupported releases
-   [The old downloads page](http://www.cgl.ucsf.edu/chimera/olddownload.html)

There are two main versions available for linux the normal version and the headless version.

## Install UCSF Chimera for a desktop computer

If you plan on using the install computer also as a desktop computer (i.e. you want to open MRC files and manipulate them in UCSF Chimera) then you should install version 1.5.3. The known version to work both in desktop mode and background mode for generating images without opening a window.

# Go to [the download page](http://www.cgl.ucsf.edu/chimera/download.html) at UCSF

# Download the *Linux* for 32bit machines and *Linux 64-bit* for 64bit machines

# Save the file to your machine and go to the directory containing the file

# Make the downloaded file executable (newer versions of the installer end with .bin instead of .exe):

    chmod 755 chimera-1.5.3-linux_x86_64.exe

# Execute the UCSF Chimera installer

    ./chimera-1.5.3-linux_x86_64.exe

# Choose a location to install the files (e.g., `/usr/local/chimera`) and let it install all of its files

# Install Chimera globally by placing a symbolic link to the executable in /usr/local/bin

    ln -s /usr/local/chimera/bin/chimera /usr/local/bin/chimera

If the stable release does not work for background mode and produces snapshots that is badly offset, we know that 1.2509 works. You may try that one.

1.  Go to [the old downloads page](http://www.cgl.ucsf.edu/chimera/olddownload.html) at UCSF and search for `1.2509`.

## Install UCSF Chimera for a server

On May 6, 2010, the UCSF Chimera team released a working version of their headless version of the program. The headless version runs the program but does not allow any interaction from the user. The version is ideal for servers, because it allows UCSF Chimera to create images of your molecule without having to install X windows.

# Download the latest Daily Build of the headless version (hopefully a working release will be provided soon)

# Go to [the main download page](http://www.cgl.ucsf.edu/chimera/download.html)

# Select the *Headless Linux 64-bit* or *Headless Linux* version of UCSF Chimera under the **Unsupported Releases** section

# Download the executable
http://www.cgl.ucsf.edu/chimera/cgi-bin/secure/chimera-get.py?file=linux_x86_64_osmesa/chimera-1.6.2-linux_x86_64_osmesa.bin

# Rename the file from .bin to .exe extension

# Make the downloaded file executable:

    chmod 755 chimera-1.6.2-linux_x86_64_osmesa.exe

# Execute the UCSF Chimera installer

    ./chimera-alpha-linux_x86_64_osmesa.exe

# Choose a location to install the files (e.g., `/usr/local/chimera`) and let it install all of its files

# Install Chimera globally by placing a symbolic link to the executable in /usr/local/bin

    ln -s /usr/local/chimera/bin/chimera /usr/local/bin/chimera

## Test UCSF Chimera

The only way to test if UCSF Chimera is working within Appion is to have Appion completely installed.

[< Install Xmipp](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_Xmipp) | [Install Grigorieff lab software >](/appion/Install_Grigorieff_lab_software)
