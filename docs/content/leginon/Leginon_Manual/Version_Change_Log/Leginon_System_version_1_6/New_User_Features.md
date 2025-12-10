## General

-   The settings window gui can all fit in 12" laptop display now

## Acquisition/Navigator Class

The following applies to an acquisition node that uses the navigator to move to its
target:

-   Based on a threshold, Targets can either be aborted or forced to collect when the
    multiple move failed to reduce further before reaching the goal.


-   It is possible to improve the targeting accuracy with a combination of stage
    movement and final image shift. However, this requires specific relationship between
    the acquiring presets and parent image presets. It works currently only for tomography
    and depth-first traversal MSI scheme.

## BeamFixer Class (New)

Simple beam shift adjustment to correct unstable beam position in long runs.

## BeamTiltImager Class (New)

Visual aid to coma-tilt alignment. It is used to acquire images of beam tilt
difractogram tableau. The user can then click at the location of the tableau where he/she
considers as the coma-free and therefore adjust the beam tilt. See Node Description Chapter
for details.

## Corrector Class

-   A bad pixel region can be specified by clicking the corners and added to the bad
    pixel plan


-   Extreme intensity pixels can be found by a click on this tool![](images/stagelocations.png)


-   Normalization image of the chosen camera configuration can be displayed.

## DriftManager Class

-   A timeout for drift monitoring can now be specified so that if the drift is
    incorrectly detected due to an empty imaging area, the acquisition of the target will
    be aborted.

## DTFinder Class (New)

Dynamic template finder is developed for tissue section imaging. An initial template is
defined by the user. The subsequent images it receives are then shifted and rotated against
the template to find the best match to the section so that the target selected on the
template can be transferred on to the new image.

## FFTMaker Class

-   Power Spectrum is displayed if processed.


-   Option for calculating power spectrum but not saved to disk.


-   Option for calculate a truncated power spectrum to speed up the calculation for
    large images.

## GridEntry Class (New)

Direct entry of grid information to Leginon database to organize the data acquired. The
main use is for simple one-pass grid screening of multiple grids when the robot does not
exist.

## ImageProcessor Class (New)

Base class for process images of a completed image target list. Mainly used for
development of batch processing of the images acquired such as image stack creation of a
tilt series. An example of its use is in filenames.py.

## ManualAcquisition Class

-   The acquired image can be sent to FFTMaker.

## PresetsManager Class

-   Preset Beam Ajustment Tool allows easier semi-automated adjustment of multiple
    presets at the same magnification.

## PixelSizeCalibrator Class

-   Power spectrum calculated from acquired image is displayed.


-   Distances measured between diffraction spots are used for an user-interactive
    pixel size calculation and averaging.

## Robot2 Class (Replacing Robot)

This class replaces Robot Class in all applications. It commnunicates to grid handling
robot(s) through database. A few default settings are changed to reflect it and also the
more general usage

-   Simulate Robot Insert/extraction = True


-   Default Z Position = 0

## TargetFilter Class

-   The images and targets that are filtered are displayed.


-   User inspection and editing of the filtered targets are allowed.

## Tomography Class

-   Allow the model to remain fixed to the initial values.


-   Separate goniometer models for positive and negative tilts.


-   Options that are not found useful are removed.

## TransformManager Class (New)

This class will eventually handle the transformation of an old target to a new one for
reacquisition after shift, tilt, and/or rotation in the grid plane. The current use is to
replace the shift adjustment in Drift Manager. As an option, it can transform targets based
on more than just its parent but all direct ancestors which makes the range of shift it can
handle much larger than the original drift manager implementation.

[< pyScope Change](/leginon/Leginon_Manual/Version_Change_Log/Leginon_System_version_1_6/PyScope_Change) | [Updated Applications (All) >](/leginon/Leginon_Manual/Version_Change_Log/Leginon_System_version_1_6/Updated_Applications_All)
