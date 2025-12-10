Many preferences for nodes in "MSI-Tomography" application are the same as in MSI with queuing option. The example here is based on a working condition at the Jensen Lab.

The following should be set up by the user "administrator" which will then be used as system-wide default preference for new users. Once the new user starts the application, he/she can customize his/her own preferences. Not all preference has independent function. Therefore if you change one preference, check for the preference(configuration) of other nodes that might depend on it.

## Nodes that acquires images/Settings> except Tomography node

This application is normally used exclusively with the queuing option. Therefore, "wait for a node to process the image" option is always off. Note that the Process target type is default in all nodes except "Tomography Preview".

### Table 16.4. Example MSI-Tomography node setup (Except Tomography node)

  Node name:           preset:   move type (to reach the preset) :   wait for a node to process the image:   publish and wait for rejected targets:   adjust target for shift:   Process target type:
  -------------------- --------- ----------------------------------- --------------------------------------- ---------------------------------------- -------------------------- ----------------------
  Grid Targeting       gr        N/A                                 N/A                                     N/A                                      N/A                        N/A
  Grid                 gr        modeled stage position              no                                      no                                       no                         acquisition
  Square Q             sq        modeled stage position              no                                      no                                       no                         acquisition
  Hole Q               hl        modeled stage postion               no                                      yes                                      yes                        acquisition
  Z Focus              hl        modeled stage position              no                                      no                                       yes                        focus
  Tomography Preview   preview   modeled stage position              no                                      no                                       yes                        preview
  Tomo Focus           fc        modeled stage position              no                                      no                                       yes                        focus

*Remember to press the "+" button in order to assign a preset to a node.*

Leave other setting options to default. These default options are:

-   Wait 2.5 seconds before acquiring image


-   Save image to database = yes


-   Mover = Presets Manager

## Presets Manager

-   Defaults are used in settings


-   The cycle order should match the sequence of data acquisition to minimize hysterisis. If the presets are imported from previous session, the cycle order is imported automatically. The example Tomography application uses gr~~[sq]{style="text-align:right;"}~~>hl~~[fa]{style="text-align:right;"}~~>fc~~[tomo]{style="text-align:right;"}~~>preview.

## Settings that are the same as in other MSI applications in queuing mode

-   Grid Targeting


-   Square Targeting


-   Hole Targeting (Queuing=yes, User verification=yes)


-   Tomography Targeting (set up as in Hole Targeting; Queuing=yes, User verification=yes)


-   Z Focus (See next sections for an example focus sequence settings)


-   Focus (See next sections for an example focus sequence settings)

## Z Focus node focus sequence example

Enter 3 focus steps in the sequence list box by typing the name in the entry box and press "+" on its right.

Select individual step in the list box and set the following parameters

### Table 16.5. Example MSI-Tomography Z Focus Steps

  Step:             preset:   focus method:   Enabled:
  ----------------- --------- --------------- ----------
  Stage_Tilt_Auto   hl        Stage Tilt      Yes
  Beam_Tilt_Auto    hl        Beam Tilt       Yes
  Manual_after      fc        Manual          No

For Stage_Tilt_Auto Step:

-   Tilt = 5 deg each direction


-   Image registration = phase correlation


-   Fit limit = 5000


-   Correct for delta Defocus/Z between 0 and 5e-5 meters


-   Correction type = Stage Z


-   Reset defocus = Default


-   Check drift = No.


-   Stigmator correction = No


-   Stigmator Defocus Min = N/A


-   Stigmator Defocus Max = N/A

For Beam_Tilt_Auto Step:

-   Same as Stage_Tilt_Auto, except:
     
    -   Tilt = 0.01 radian each direction

## Tomo Focus node focus sequence example

Enter 3 focus steps in the sequence list box by typing the name in the entry box and press "+" on its right.

Select individual step in the list box and set the following parameters

### Table 16.6. Example MSI-Tomography Tomo Focus Steps

  Step:             preset:   focus method:   Enabled:
  ----------------- --------- --------------- ----------
  Stage_Tilt_Fine   fa        Stage Tilt      Yes
  Beam_Tilt_Fine    fa        Beam Tilt       Yes
  Manual_after      fc        Manual          No

For Stage_Tilt_Fine Step:

-   Tilt = 1 deg each direction


-   Image registration = phase correlation


-   Fit limit = 5000


-   Correct for delta Defocus/Z between 1e-07 and 5e-5 meters


-   Correction type = Stage Z


-   Reset defocus = Default


-   Check drift = No.


-   Stigmator correction = No


-   Stigmator Defocus Min = N/A


-   Stigmator Defocus Max = N/A

For Beam_Tilt_Fine Step:

-   Same as Stage_Tilt_Auto, except:
     
    -   Tilt = 0.01 radian each direction
         
    -   Correct for delta Defocus/Z between 0 and 5e-5 meters
         
    -   Wait for drift to be less than 1.2e-9 m/s

## Tomography

Tomography has many unique settings:

1.  General Acquisition Settings:
     
    -   Use "modeled stage position" to move to target.
         
    -   Wait 2.5 seconds before acquiring image
         
    -   Save image to database
         
    -   Float->Integer = No (There is a better settings in the lower panel of the node)
         
    -   Correct image = Yes
         
    -   Wait for a node to process the image = No
         
    -   Publish and wait for rejected targets = Yes (For focusing before acquisition)
         
    -   Publish and wait for the reference target = No (unless the beam is not stable, and a beam shift fix is required before most tilt series acquisition)
         
    -   Adjust targets for drift = Yes
         
    -   Declare drift between targets = Yes ( to ensure proper targets of multiple targets on the same lower mag hl image)
         
2.  Acquisition Presets Order = tomo
     
3.  Acquisition Mover Settings (See Session on Different ways to move targets in the MSI chapter for details on how to optimize these settings:
     
    -   Mover: Navigator
         
    -   Navigator Target Tolerance: 6e-08 m (Scope performance dependent. Use a larger value if the stage fails to reach the default value in acceptable, for example, 5, trials).
         
    -   Navigator Acceptable Tolerance: 2e-07 m (Targeting accuracy dependent)
         
    -   Final Image Shift = Yes
         
4.  Tilt
     
    -   Parameters Min.,Max.,Start
         
    -   Step >0: start from "Start" tilt stepping to "Max" then from "Start" tilt stepping to "Min"
         
    -   Step <0: start from "Start" tilt stepping to "Min" then from "Start" tilt stepping to "Max"
         


1.  Exposure (See more in [Set up dose parameters in Tomography](/leginon/Leginon_Manual/Preferences_Setup/MSI-Tomography_Preferences/Set_up_dose_parameters_in_Tomography))
     
    Tomography node divides the total dose by the number of tilt images it needs to acquire to calculate the real exposure time it uses, given the limit set by the user.
     
    -   Total dose=200 e-A^2
         
    -   Exposure time Min.=0.25 seconds
         
    -   Exposure time Max.=2 seconds
         
2.  Before Collection
     
    -   Run buffer cycle=Yes
         
    -   Align zero loss peak=No (Yes if energy filter is used)
         
    -   Measure dose=Yes
         
3.  Misc.
     
    -   Scale to convert to integer = Yes (Determine the scale factor by your camera sensitivity and the exposure intensity of each tilt image. See the session on Import Notes about Image Intensity Recorded through Tomography Node below)
         
    -   Consider images with less than "100" counts of the first image as obstructed. (Determined by camera sensitivity and conversion scale above since the number is post-conversion. In general, 50% of a normal untilted image intensity is reasonable)
         
    -   Abort if first half collected less than "90" % of images. (Reduce this number if fewer tilts are acceptable)
         
    -   The rest of the settings are various ways to detect the shifts of the images at adjacent tilts. Some are experimental. The most reliable is the Option "Use lpf in peak finding of tilt image correlation".
         
4.  Model
     
    The goniometer model that predicts the defocus drift as a result of offset goniometer tilt axis relative to the detector imaging axis can be dynamically fitted. The following parameters are used to initialize the model fitting of the goniometer tilt axis. See Session on low magnification model fitting for more details.
     
    -   The model can be initialized using existing model in the database either at the same magnification of the tomo preset, at the first available model at lower magnification, or a specified magnification for larger range of flexability, or custom values set in this node.
         
    -   Custom Tilt Axis Model is set separately for the two direction of the alpha tilt since many stages behaves differently as the weight of the stage lean on different part of the goniometer.
         
    -   During a dynamical model fitting, the fitting modifies the predicted stage z offset(z0) from the data at each tilt. To avoid false fitting that predicts an unreasonable z0, a limit can be added to allow a change of a physically possible value such as 2 um. This limit should be relaxed when the tilt axis model is unknown and is expected to be far from the initial guess.
         
    -   Keep the tilt axis parameters fixed = No if the stage tilt axis angle from y axis of the detector and the offset of the tilt axis from the center of the detectors are dynamically fitted during the tilt axis.

Once the goniometer model gives satisfactory results, Keep the tilt axis parameters fixed is recommended with the model set to be initialized with the model of "only this preset"

Defocus prediction smoothing is default to use shifts of 4 tilt images. A larger number can be set if the goniometer behavior is particularly jiggly.

## Dose Measurement and Align ZLP

Use defaults:

-   Use "stage position" to move to the reference target


-   Wait "3" seconds before performing request


-   If reguest performed less than "900" seconds ago, ignore request

[< Initial MSI application preference setup](/leginon/Leginon_Manual/Preferences_Setup/Initial_MSI_application_preference_setup) | [Robot MSI-Section preference set-up >](/leginon/Leginon_Manual/Preferences_Setup/Robot_MSI-Section_preference_set-up)
