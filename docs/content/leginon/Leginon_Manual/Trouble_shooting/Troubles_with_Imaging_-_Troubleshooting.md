## Image is acquired but contains no real information

Commonly Why:

-   Main screen at the scope is down


-   Camera is not inserted (Gatan camera)


-   Digital Micrograph program is not running (Gatan camera)


-   Shutter switch box is set to CM, i.e., to collect film data only (Tietz camera)

## Image is acquired but contains artifacts either in image or in Fourier Transform

Commonly Why:

-   Beam is partially covering the CCD.


-   Scope viewing window is not covered and room light is on


-   Dark/Bright images are not available or need to be reaquire.


-   Bias level and quadrant correction may need to be reset (Digital Micrograph and Gatan camera)

## Can not read reference images that were acquired by other users

Commonly Why: You don't have permission to read their image files

Solution:

-   Have the person change the group or even world permission for reading the data directory and the image files in it.

The person is not around when this happens:

Acquire your own reference images at the camera setting that needs the dark and bright images. However, Leginon always look for the most recent calibration in the database by anyone. Every user will have to do this everytime if the permission problem is not solved.

## Beam shifts away from imaging area over time

Commonly Why:

-   Residual lens hysteresis if you haven't allowed the scope to warm up for HM mode after acquiring LM atlas.


-   Focus correction has taken the absolute focus point far away from U-centric focus.

### Solutions:

-   Wait until the optics is stabilized


-   Activate "Publish and wait for the reference target" in Exposure Node. This will enable "Fix Beam" node to search for the beam in the desired range and shift the beam to the best result. A reference target, normally an empty square, need to be selected on the grid to use this function. See description in the node description chapter for usage.
-   Pause MSI and correct for residual beam shift
     
    1.  Pause before next hole or square by clicking Hole/Toolbar>Pause button (Pause icon) or Square/Toolbar>Pause button (Pause icon), respectively. Which one to pause depends on what is the next target.
         
    2.  Leginon/Presets Manager> When the acquisition sequence is stopped, send the preset that has beam shift problem "To Scope" (ToScope icon).
         
    3.  Leginon/Navigation/Toolbar> Choose move type to be "Beam Shift" and make sure "Use Camera Configuration" is unchecked in settings.
         
    4.  Leginon/Navigation> "Navigate"*(navigate icon) to center the beam. If "Navigate" does not bring the beam in, manually shift the beam at the microscope. Do not forget to lift the screen and cover the viewing area after done.
         
    5.  Leginon/Presets Manager> save the new beam shift by retrieving it "From Scope" (From Scope icon).
         
    6.  "Continue" data collection on next hole or square target by clicking Hole/Toolbar> "Continue" button or Square/Toolbar> "Continue" button, respectively.
         
        "Navigate" means selecting the navigate tool on the top right of image display and then single-left-clicking the location of the new center that is translated by the given TEM Parameter.


-   Reset the defocus=0 point back to U-centric focus.
     
    Leginon reset defocus after each defocus correction. Therefore, the point where the user defines as defocus=0 may drift away from U-centric focus over time or after a very large correction before it is reset to U-centric focus by z focus correction.
     
    1.  Pause before next hole or square by clicking Hole/Toolbar>Pause button (Pause icon) or Square/Toolbar>Pause button (Pause icon), respectively. Which one to pause depends on what is the next target.
         
    2.  Leginon/Presets Manager> Send "hl" preset "To Scope" (ToScope icon).
         
    3.  Leginon/Z Focus/Toolbar> Send stored U-centric focus to scope.
         
    4.  Leginon/Z Focus/Toolbar> Reset defocus to 0
         
    5.  Scope> U-center the stage if it is very out of focus.
         
    6.  Leginon/Presets Manager> Send the preset that showed bad beam shift "To Scope"
         
    7.  Scope and Leginon/Presets Manager> Check the beam shift, make correction, and then retrieve the correct value "From Scope"
         
    8.  Leginon/Drift Manager> Declare Drift (declare drift icon) to force correction at next possible point in the process.
         
    9.  "Continue" data collection on next hole or square target by clicking Hole/Toolbar> "Continue" button or Square/Toolbar> "Continue" button, respectively.

## Beam shifts away from imaging area only when targeting move type is image shift

Commonly Why:

-   Image/Beam Shift calibration on the microscope is not optimal


-   Defocus is very far from eucentric focus

### Solutions:

-   Bad Image/Beam calibration
     
    Follow instruction for performing the calibration for FEI Tecnai machines under Alignments/Image HM-TEM(or LM)/Image-Beam calibration
     
    1.  Pause before next hole or square by clicking Hole/Toolbar>Pause button (Pause icon) or Square/Toolbar>Pause button (Pause icon), respectively. Which one to pause depends on what is the next target. If in queuing mode, pause at the node that process the queue.
         
    2.  Scope> move to an unimportant area or pull the holder out enough to allow the beam to go through.
         
    3.  Scope> reset defocus to eucentric height.
         
    4.  Scope> Follow instruction for performing the calibration for FEI Tecnai machines under Alignments/Image HM-TEM(or LM)/Image-Beam calibration.
         
    5.  Leginon/Presets Manager> Cycle the presets a few times. The calibration takes the scope to conditions outside the presets, and can cause strong hysteresis if this step is not done.
         
    6.  Leginon> Follow the procedures for confirming and saving good image shift at various presets.
         
    7.  "Continue" data collection on next hole or square target by clicking Hole/Toolbar> "Continue" button or squares/Target Toolbar> "Continue" button, respectively.
         
        "Navigate" means selecting the navigate tool on the top right of image display and then single-left-clicking the location of the new center that is translated by the given TEM Parameter.


-   Defocus far from eucentric focus
     
    Image/Beam shift coupling worsens when the defocus is away from where it was calibrated. If, after the above calibration, the problem remains during MSI acquisition, additional focusing sequence should be added at lower magnification that move the stage to close to eucentric height so that the image shift target is selected
    on an image of a close-to-eucentric location.
     
    1.  Leginon/Z Focus/Focus Sequence> activate both Stage_Wobble and Z_to_Encentric steps.
         
    2.  Leginon/Hole (or Subsquare) Targeting> selection a focus target if not already done so when a newly acquired sq image comes in.

If the accuracy of moving stage to eucentric height by the focus sequences in "Z Focus" is still not sufficient. Add another focus step performing the same task as Z_to_Encentric step. Repeating beam-tilt based autofocusing often improve the accuracy unless the calibration is off.

Still not working: You have chosen a target that requires too much image shift for an independent image shift from beam shift. This is necessary when the lower mag targetting is not good either because the preset image shifts are not aligned or the stage position movement is not properly modeled.

Solution: For image shift problem see solution for "Target is consistently off in the same direction and distance". For stage model problem, see "Modeled stage calibration" in setup notes.

## Beam shifts away from imaging area when targeting move type is stage movement

Commonly Why:

-   U-center defocus not set to 0 in LM mode.


-   LM alignment such as rotation center is way off.

Solution: Check and correct microscopic alignment error. Preset parameters checking and reset may be necessary after the correction.

Comments: If the problem persist, the original stage matrix calibration may have been performed with a bad alignment. The calibration should be redone with a well-aligned scope in LM mode.

## Objective aperture appears off in "sq" preset when it is centered in HM mode

Commonly Why:

-   U-center defocus not set to 0 in LM mode.


-   LM alignment such as image shift is way off.

Solution: Check and correct microscopic alignment error. Preset parameters checking and reset may be necessary after the correction.

## The specimen appears over-dosed in the high magnification images or the dark correction image has a high value (while using a Gatan CCD)

This issue may occur when the shutter is incorrectly configured through Digital Micrograph (the imaging software for the Gatan CCD that resides on the TEM computer) or simply a bad dose calibration or too long an exposure time. To issue these corrections:

# Set the "shutter" to "Auto" on the external control box attached to the TEM.
 

# Open Digital Micrograph on the Microscope computer and go to the Camera Set-up page.
 

-   Go to Configuration
     
-   Set the Primary Shutter to Pre-specimen
     
-   Set the Alternate Shutter to Post-specimen
     
-   Set the Default Primary Shutter to the Normally Closed position.

## The exposure image has a circular imprint of the beam at the size of the preset used for melting the ice

This issue may occur when the main screen is left up during very long (such as over 30 sec) ice melting and at high HT. Leginon has a mechanism that put the screen down during ice melting. It is caused by over-saturating the Phosphur layer on the CCD. If you see this effect, the screen may have failed to lower. Please test it by observing the screen movement with simulating target in any focuser node that has ice melt time set not to zero. Report the problem back to the leginon team if you are sure it is not your scope's problem.

## Dose measurement image for a preset is not gain/dark corrected even though the image acquired by the preset is corrected

Dose measurement tool in Presets Manager uses a smaller camera dimension to save the time required for the image acquisition since the operation is typically performed on preset that uses the full dimension and minimal binning of the camera. The size it uses is user-defined. You can check what that is in Preset_Manager/Settings> ![](images/settings.png).

For example, if your preset uses dimension of 2048 x 2048 and binned by 2 on a 4kx4k camera, and the dose image size setting is 512, the dose image taken would be 512 x 512 binned by 2 image centered on the camera. The exposure time will be identical to the preset.

If the bright/dark images for this special camera configuration has not been acquired previously, the dose image would be uncorrected and the dose measurement value will be incorrect.

[< Hardware Troubles](/leginon/Leginon_Manual/Trouble_shooting/Hardware_Troubles) | [Troubles with Targeting >](/leginon/Leginon_Manual/Trouble_shooting/Troubles_with_Targeting)
