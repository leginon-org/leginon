-   [Python installer fails on pyScope and numExtension for
    Windows](/leginon/Leginon_Manual/Installation_Troubleshooting/InstallationUpdate_problems#Failed-pyScope-numExtension-Window-installation-through
    python)


-   [Not all files are updated](/leginon/Leginon_Manual/Installation_Troubleshooting/InstallationUpdate_problems#Incomplete Leginon update)


-   [New Group/User added does not show up in the selection
    list in Web Leginon Administration Tool](/leginon/Leginon_Manual/Installation_Troubleshooting/InstallationUpdate_problems#Incomplete Leginon update)


-   [I can't install SciPy/NumPy on SUSE](/leginon/Leginon_Manual/Installation_Troubleshooting/InstallationUpdate_problems#Installation without a class of nodes)


-   [Something is not showing in Web viewer or the
    administration tool components](/leginon/Leginon_Manual/Installation_Troubleshooting/InstallationUpdate_problems#SciPy Installation failed in SuSE)


-   [Stage does not move after a pyScope update on the
    computer controlling the microscope](/leginon/Leginon_Manual/Installation_Troubleshooting/InstallationUpdate_problems#Display errors on webviewer and web administration tools)

## Failed pyScope numExtension Window installation through python

***Why:***

-   Specially compiled pyScope and numExtension are needed to comunicate with Gatan
    CCD camera. Currently we only have them compiled for python2.5

Solution: Download and use python2.5 and use the window-installer in win-install
folder (start by double-clicking them) not "python setup.py install".

## Incomplete Leginon update

This normally happens to files that you have modified in the previous version.

***Why:***

-   unknown

Solution: Remove the old installation first.

-   Find the location of your Leginon installation. Once you have tried,even
    unsuccessfully, to install Leginon. You can use the following command to find
    the directory:


    Linux> cd
    Linux> start-leginon.py -v

    Window> Go to \All Programs\Leginon\Leginon Folder from your Start Menu

-   Go to the directory above it. This is normally the site-package directory
    under your python installation


    Linux> rm -r Leginon
    Window> drag the Leginon folder to Recycle Bin

-   Redo Leginon installation.

## Installation without a class of nodes

If you encounter a problem with node classes that you don't actually use, you may avoid
loading the codes with the following modification:

-   Fnd the location of your Leginon installation


    Linux> cd
    Linux> start-leginon.py -v

-   go to the subdirectory of noderegistry


    Linux/home> cd leginon_directory/noderegistry

-   edit the file "default.ncr" to coment out the registry of the class of nodes that
    you do not need (Tomography node class in this example):


    #[Tomography]
    #module: tomography
    #type: Pipeline
    #package: tomography

## SciPy Installation failed in SuSE

SciPy may not build properly on some versions of SuSE due to an incompatible LAPACK
package that comes with SuSE. You can get scipy as well as a compatible LAPACK etc. from
http://repos.opensuse.org/science (need to specify your SuSE version and machine etc.

## Display errors on webviewer and web administration tools

To display error and report them to get help for the php, including mysql-php and mrc
extension, do the following:

-   Find your php.ini the following parameters and change them accordingly:


    display_errors = On
    error_reporting  =  E_ALL &amp; ~E_NOTICE

-   Restart your apache server


    > /etc/init.d/apache2 restart

-   From your webbrowser, refresh the problematic page. If you don't know what to do
    with it, report it when you ask for help.

[< Getting Help](/leginon/Leginon_Manual/Installation_Troubleshooting/Getting_Help) | [Administration Tool problems >](/leginon/Leginon_Manual/Installation_Troubleshooting/Administration_Tool_problems)
