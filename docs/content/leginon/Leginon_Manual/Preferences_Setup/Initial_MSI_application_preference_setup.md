Many of the preferences are matched to the function of the nodes and therefore are more like configuration. Starting from v1.5, the "Leginon-Appion Administrator" default preferences are loaded during the installation ready for standard MSI operation assuming the use of example preset names and properties. This means that as a new user, you can use these straight away as long as the calibration required are made.

If you mess up your settings too badly that it does not run any more, you may [revert back to your institution default](/leginon/Leginon_Manual/Administration_Tools/Default_Settings) easily.

The following is the comprehensive list of what is set as default during the initial loading for basic MSI-T, MSI-Edge, and MSI-Raster applications. In some cases, the reason behind the setting is also included. Each institution can alter these default values according to their particular need for all their new users by making the changes as "Leginon-Appion Administrator" user.

Table 16.1 Example MSI node setup

  Node name:       preset:      move type (to reach the preset) :   wait for a node to process the image:   publish and wait for rejected targets:   adjust target using ancestor:
  ---------------- ------------ ----------------------------------- --------------------------------------- ---------------------------------------- -------------------------------
  Grid Targeting   gr           N/A                                 N/A                                     N/A                                      N/A
  Grid             gr           modeled stage position              no                                      no                                       no
  Square           sq           modeled stage position              yes                                     no                                       no
  Hole             hl           modeled stage postion               yes                                     yes                                      one
  Z Focus          hl or fc*   modeled stage position              no                                      no                                       one
  Exposure         en & ef      image shift                         no                                      yes                                      one
  Focus            fc           image shift                         no                                      no                                       one

* *Use hl if your z focus target will be at the center of a hole where its fft image don't have obvious Thone rings. Use fc if the target is on carbon film for better accuracy.
 
Leave other setting options to default. These default options are:
 

## Wait 2.5 seconds before acquiring image
 

## Save image to database = yes
 
Remember to press the "+" button in order to assign a preset to a node._
 

* Presets Manager/Settings>
 
paus time between preset changes = 1 sec.
 
Cycle presets = yes
 
Optimize preset cycle = yes
 
Cycle Magnification Only = yes
 
The cycle order should match the sequence of data acquisition to minimize hysterisis. If the presets are imported from previous session, the cycle order is imported automatically. As an example, the cycle for naming scheme used here at NRAMM is gr -> sq -> hl -> fa -> fc -> en -> ef.
 

* Grid Targeting/Settings>
 

1.  Select Preset = gr
     
2.  Label =
     
    *Enter a new label for each new atlas that is acquired for this session. The first atlas requires no label. This label will be included in the image file name; therefore, shorter names are preferred.
     
3.  Radius = 0.0009 m covers about the whole grid.
     
4.  Mosaic center = stage center

-   Square Targeting/Settings> Ignore all settings. No need to set these general targeting finding configuration


-   Square Targeting/Mosaic Settings>
     
    1.  Calibration Parameter = stage model position
         
    2.  Scale Image = yes (default)
         
    3.  Scale Image pixel size = 512 (or the size of the grid image that will be used to build the atlas). A larger value can be used in future loading of the tile list.


-   Hole Targeting/Settings and Exposure Targeting/Settings>
     
    1.  Allow for user verification of picked holes = yes
         
    2.  Queue up targets= no
         
    3.  Declare drift when queue is submitted = yes (default)
         
    4.  Skip auto picking of holes = yes (change to No after proper setup of the hole-finding algorithm)


-   Focus/Settings> and Z Focus/Settings>
     
    1.  Acuire post-focus image = yes
         
    2.  Melt time = 0 second (should be customized for each grid)

Table 16.2 Example MSI Focus Setup

  Step:              preset:   focus method:   correction type:   Enabled:
  ------------------ --------- --------------- ------------------ ----------
  Z_to_Eucentric     fa        Beam Tilt       Stage Z            No
  Def_to_Eucentric   fa        Beam Tilt       Defocus            Yes
  Manual_after       fc        Manual          N/A                Yes

-   Focus/Focus Sequence>
     
    Enter 3 focus steps in the sequence list box by typing the name in the entry box and press "+" on its right.
     
    Select individual step in the list box and set the following parameters
     
    For both autofocus steps:
     
    1.  Tilt = 0.01 radian each direction
         
    2.  Image registration = phase correlation
         
    3.  Fit limit = 1000
         
    4.  Correct for delta Defocus/Z between 0 and 2e-5 meters
         
    5.  Check drift greater than 3e-10 meters/s (should be customized by the user based on the exposure time and required resolution).
         
    6.  Stigmator correction = No (typical) Yes (if well calibrated)
         
    7.  Stigmator Defocus Min = 2e-06 meters
         
    8.  Stigmator Defocus Max = 4e-06 meters

Table 16.3 Example MSI Z Focus Steps.

  Step:            preset:      focus method:   Enabled:
  ---------------- ------------ --------------- ----------
  Stage_Wobble     sq           Stage Tilt      No
  Z_to_Eucentric   hl           Beam Tilt       Yes
  Manual_after     fc or hl*   Manual          Yes

-   Z Focus/Focus Sequence>
     
    The setup here works well for holey carbon grids. Continuous carbon with negative stain may require a different Z Focus Sequence because its low contrast at intermediate mag. See the Chapter on MSI-Raster application regarding improving autofocus.
     
    Enter 2 focus step in the sequence list box by typing the name in the entry box and press "+" on its right.
     
    Select individual step in the list box and set the following parameters
     
    *Use hl if your z focus target will be at the center of a hole where its fft image don't have obvious Thone rings. Use fc if the target is on the carbon film for better accuracy.

For "Stage_Wobble" Step:
 

## Tilt = 2 degrees each direction
 

## Image registration= phase correlation
 

## Fit limit = N/A
 

## Correct for delta Defocus/Z between 0 and 0.0002 meters
 

## Correction type = Stage Z
 

## Check drift greater than 3e-10 meters/s = No
 

## Stigmator correction = No
 

## Stigmator Defocus Max/Min = N/A

For "Z_to_Eucentric" Step:
 

## Tilt = 0.01 radian each direction
 

## Image registration= phase correlation
 

## Fit limit = 1500
 

## Correct for delta Defocus/Z between 0 and 0.0002 meters
 

## Correction type = Stage Z
 

## Reset defocus = Default
 

## Check drift greater than 3e-10 meters/s = No
 

## Stigmator correction = No
 

## Stigmator Defocus Max/Min = N/A

[MSI-Tomography Preferences >](/leginon/Leginon_Manual/Preferences_Setup/MSI-Tomography_Preferences)
