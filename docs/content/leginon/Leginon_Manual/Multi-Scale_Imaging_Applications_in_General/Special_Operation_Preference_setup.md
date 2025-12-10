## Taking final exposures at very high magnification

Hysteresis of image shift at very high mags such as 200 kx can be reduced by setting the following configuration

1.  Presets Manager/Settings>
     
    Cycle Magnification Only = no
     
2.  If [queuing is used at exposure targeting](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Queuing_Example_1_-_Exposure_Targeting),
     
    Exposure Targeting/Settings>
     
    Declare drift when queue submitted = yes

## Avoiding drift correction that uses LM sq preset

If the grid is flat and the offset of targets is small enough that it can be corrected in the hole image, we recommend using the [Queuing option at Exposure Targeting](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Queuing_Example_1_-_Exposure_Targeting). The sq preset is still used after Stage Z adjustment to correct the hole targets but will not be used when queued exposure targets are processed.

If the offset of targets is minimal even after stage Z adjustment, set the following to avoid using ancestor images obtained in LM for drift management purpose, queuing or not.

1.  Target Adjustment/Settings>
     
    Minimum Magnification =Lowest Magnification you want to allow the node to use for determining the new target.

## Minimize the use of image shift for the final exposure (Approach 1)

Large image shift can cause sufficient beam tilt that creates problems such as bad autofocus, beam shift, and loss of resolution (but probably only if better than 4 angstrom is needed). Image shift is used in Leginon for targeting exposure because it is much more accurate than a single movement by the specimen goniometer, even after it is modeled for mechanical periodicity.

The accuracy of the stage movement is lower when it moves a long distance. Therefore, using iterative stage movement can improve the targeting, and therefore reduce the amount of image shift required for the final exposure. To use this feature, change the following preference in Hole node (or Subsquare node in MSI-Raster).

It is important to know that in order to check whether the precision is reached, image is taken at the preset at which the target is selected on (in this case, sq preset), so the dose should be kept at minimal. On our microscope 0.2 micron precision can be obtained within 2 to 3 moves.

Hole/Settings/Image Acquisition>

# Mover=navigator
# Navigator Target Tolerance = 2 e-7 m (or whatever tolerance you like): This sets the goal for multiple movement
# Navigator Acceptable Tolerance = 1 e-6 m (or whatever tolerance you like): If further movement causes an increase rather than a decrease of targeting accuracy, this value determines whether the target is aborted or not.
# Final Image Shift = No
# Adjust target using "No" ancestor

Navigation/Settings/Error Checking and Correction>

# Preset cycle after each move = yes if your sq preset is in LM mode and you don't mind wait a little longer; = no if you don't have hysteresis problem staying in sq preset for the unknown amount of time during the iterative move.

## Minimize the use of image shift for the final exposure (Approach 2)

A different approach is being developed to minimize image shift while maintaining final targeting accuracy-A combination of stage movement and image shift. This approach can only be used in limited cases such as targets selected for the tomography node or exposure node, and is only experimental in the latter case.

Tomography or Exposure/Settings/Image Acquisition>

# Move Type = modeled stage position
 
# Mover=navigator
 
# Navigator Target Tolerance = 1 e-7 m (or whatever tolerance you like)
 
# Navigator Acceptable Tolerance = 1 e-6 m (or whatever tolerance you like)
 
# Final Image Shift = Yes

## Optimize autofocusing sequence

The focus sequence in Focus and Z Focus nodes can and should be optimize for specific cases. The activated sequence in the default setting is good for a flat holey grid and is meant for high resolution imaging at 50k x or higher. If accurate defocus is not important, focusing once per grid square may be sufficient, for which all focus sequence in Focus node can be deactivated and the same autofocus step can be added to Z Focus node instead.

There are two methods to determine the defocus automatically : Stage tilt (Equivalent to stage wobbling) and Beam tilt. There are also two possible ways for correcting the defocus measured: Defocus (Equivalent to turning the focusing knob on the scope and reset the defocus) and Stage Z (Moving the stage to the zero defocus height).

The following observations at NRAMM may help you determine what is the best to use:

# Both defocus determination method requires calculation correlation between two images. Therefore, the magnification and the location of the autofocusing should include area with contrast.
 
# The higher the magnification, the more accurate the defocus determination but the smaller the range of defocus the defocus determination can handle.
 
# Beam Tilt is more reproducible and preferred method to determine defocus in HM mode.
 
# Stage Tilt (Wobbling) is the preferred method to determine defocus in LM mode.

MSI-Raster Chapter contains an example of an [alternative Z Focus node focus sequence](/leginon/Leginon_Manual/Leginon_MSI-raster_Application/Improving_Autofocusing) for grid that show little contrast at medium magnifications.

[< Initial MSI application preferences](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Initial_MSI_application_preferences) | [MSI Quick-start >](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_Quick-start)
