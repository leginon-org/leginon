The changes from v1.3 includes update of all in-house components of Leginon and dbemtools,
mrctools but not the database. A new configuration file (sinedon.cfg) is required. The updated
mrctools and dbemtools installation (required) is now performed through "php devel" so that it
can be customized according to the php version installed on the web server.

## Install the supporting packages first if missing:

Follow the instruction for your specific Linux distribution.

For example, SUSE users can use YaST to install them

  -------------------------------------------------------------------------------------------------
  Name:                     Download site:
  ------------------------- -----------------------------------------------------------------------
  NumPy 1.0b5 or higher     <http://www.scipy.org>

  SciPy 0.5.1 or higher*   <http://www.scipy.org> [,
                            http://repos.opensuse.org/science](http://repos.opensuse.org/science)
  -------------------------------------------------------------------------------------------------

*SciPy may not build properly on some versions of SuSE due to an incompatible LAPACK
package that comes with SuSE. You can get scipy as well as a compatible LAPACK etc. from
http://repos.opensuse.org/science (need to specify your SuSE version and machine
etc.)

## Install php devel packages on the web server first if missing:

You can check whether php devel is installed by
typing

     >cd [webdirectory]          #/var/www/html in this example
    >phpize

Follow the instruction for your specific Linux distribution. <http://rpmfind.net/linux/RPM/Development_Languages_PHP.html> has some
examples.

For example, SUSE users can use YaST to install them

## Install the new mrctools

mrctools 1.4 will work better with Leginon 1.4 and 1.5. It is no longer included in
dbemtools and is now installed from php devel directory.

-   Download dbem tools from <http://emg.nysbc.org/software/mrctools> .


-   Follow the instruction at <http://emg.nysbc.org/software/mrctools/mrc_so.php> for installation and
    testing.

## Recommended Application Preference Changes when updated from version 1.3

## All MSI Applications

-   If the goniometer model shows strong oscillation, using modeled stage position
    movement to create and to move to targets from Grid Atlas can improve the accuracy. To
    use this new feature, you should calibrate the modeled movement at the very low mag
    preset that is used for making the atlas (gr in our convention), "mag only" is enough.
    Once it is available, Change the following preferences will allow the use of this new
    feature.


-   Grid/Settings> move type ="Modeled Stage Position".


-   Square/Settings> move type ="Modeled Stage Position".


-   Square Targeting/Mosaic> Calibration parameter="Modeled Stage
    Position".


-   The new melting preset should be chosen in Focus node or any other node that
    melting is required.


-   Focus/Settings/Focusing> Melt preset=fc


-   To correct the Focuser/DriftManager toggling problem, Drift Manager pause time
    before the first image acquisition should be determined per microscope. For example,
    TecnaiF20 at NRAMM requires about 4 sec, but Spirit 12 requires 12 sec. If the stage
    is stable and well below the drift threshold most of the time, a shorter pause can be
    used to reduce the total monitoring time at the expense of allowing some toggling when
    it ocasionally goes above the threshold.


-   Drift Manager/Settings/Drift Management> Wait at least "4" seconds between
    images.

## Calibration

None

## Manual

None

[Upgrade to Leginon System version 16 ^](/leginon/Leginon_Manual/Upgrade_Instructions/Upgrade_to_Leginon_System_version_16)
