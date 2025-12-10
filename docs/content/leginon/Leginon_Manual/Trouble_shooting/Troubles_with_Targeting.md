## Quick Links

-   [Targeting is consistently off in the same direction and distance](/leginon/Leginon_Manual/Trouble_shooting/Troubles_with_Targeting#Targeting-is-consistently-off-in-the-same-direction-and-distance)
-   [Targeting is consistently off in opposite direction from where you pick](/leginon/Leginon_Manual/Trouble_shooting/Troubles_with_Targeting#Targeting-is-consistently-off-in-opposite-direction-from-where-you-pick)
-   [Hole targeting is inconsistently off or goes bad in the next round after correction](/leginon/Leginon_Manual/Trouble_shooting/Troubles_with_Targeting#Hole-targeting-is-inconsistently-off-or-goes-bad-in-the-next-run-after-correction)
-   [Hole targeting is off more when the image shift target is away from the center of the image](/leginon/Leginon_Manual/Trouble_shooting/Troubles_with_Targeting#Hole-targeting-is-off-more-when-the-image-shift-target-is-away-from-the-center-of-the-image)
-   [Automatic hole finding fails to pick up good ice thickness after set up](/leginon/Leginon_Manual/Trouble_shooting/Troubles_with_Targeting#Automatic-hole-finding-fails-to-pick-up-good-ice-thickness-after-set-up)
-   [No broken grid square for dose measurement and ZLP alignment (MSI-Tomography)](/leginon/Leginon_Manual/Trouble_shooting/Troubles_with_Targeting#No-broken-grid-square-for-dose-measurement-and-ZLP-alignment-for-MSI-Tomography)
-   [Grid mosaic is too small to see the details](/leginon/Leginon_Manual/Trouble_shooting/Troubles_with_Targeting#Grid-mosaic-is-too-small-to-see-the-details)
-   [Grid mosaic is not patched together well](/leginon/Leginon_Manual/Trouble_shooting/Troubles_with_Targeting#Grid-mosaic-is-not-patched-together-well)
-   [Grid mosaic display in Leginon is different from that of the Web Viewer](/leginon/Leginon_Manual/Trouble_shooting/Troubles_with_Targeting#Grid-mosaic-display-in-Leginon-is-different-from-that-of-the-Web-Viewer)

## Grid mosaic is too small to see the details

### Why:

-   The image scale for creating mosaic is set too small.

### Solution:

1.  Leginon/Square Targeting/Mosaic Settings> Change "Scale Image" to a larger
    size
     
2.  Leginon/Square Targeting/Mosaic Settings> Click "Apply" and then "Create" the
    mosaic atlas.

## Grid mosaic is not patched together well

### Commonly Why:

-   LM mode U-center defocus not set to 0.


-   LM mode rotation center is off.


-   Bad stage position matrix calibration

### Solutions:

1.  Correct the alignemnt error or redo stage position matrix calibration
     
2.  Acquire a new atlas
     
    -   Leginon/Grid Targeting/Setting> Enter a new label
         
    -   Leginon/Grid Targeting> Click "Calculate Atlas"
         
    -   Leginon/Grid Targeting> Click "Submit Targets" (play icon) to begin acquiring the atlas.
         
    -   Leginon/Square Targeting> Follow the atlas progress in the display.

## Grid mosaic display in Leginon is different from that of the Web Viewer

### Why:

-   The goniometer does not reach the intended position due to ,most commonly, a pole touch error that temporaily disables the goniometer.


-   The calibration used to move to the target in "Grid" node is not the same as the calibration parameter used to create the mosaic in "Square Targeting" node are not consistent.

### Solution:

-   Other than fix the goniometer, Targeting on these mosaic can still work if the error does not occur frequently enough to interfere drift management.


-   Check "Leginon/Grid/Settings/Use ?? to move to target" against "Leginon/Square Targeting/Mosaic Settings/CalibrationParameters". The latter should be changed if the mosaic is already acquire and what seen on the Web is better than what is in Leginon. The mosaic atlas can be recreated by clicking the "Create" button.

### More Explanation:

-   The web tools and Leginon main program use different mechanism to paste together the atlas.
     
    The targets Leginon "Grid Targeting" node send out is an even spaced raster. "Grid" node uses that information and the move type set for the node to calculate the goniometer position it needs to aim for in order to get to where it really wants to go to and acquires the image. It is done this way so that it can handle any complex move type. For example, lets say that the model is p=x^2 so that to get to position p' from 0, the goniometer x needs to be sqrt(p'). "Grid Targeting" send the target as p', "Grid" figure out that x'=sqrt(p') and send the x value to the scope to move.
     
    When it needs to display the atlas in "Square targeting", Leginon uses the actual goniometer position of each tile image back calculates the targeted position according to the model. This has the advantage that if there is a problem with the goniometer and the stage does not move to where it needs to (such as after a pole touch error), the tile image will appear at its actual position. In the example above, the image will appear at p' from the image because from the goniometer position x'=sqrt(p'), p=x^2=(sqrt(p'))^2.
     
    The webtool, however, pastes the atlas together using the targets saved from "Grid Targeting". It does not care what you have set in "Square Targeting" node. Therefore, it will always look right, unless of course the stage did not move to the target when it acquired the image.

## Targeting is consistently off in the same direction and distance

Commonly Why: Image shifts in "hl", "sq", or "gr"presets are not aligned with the presets at higher mags. The low mag "sq" preset is especially prone to this problem.

**Important: When the targeted image is off, it normally means the image shift of the preset where the target comes from is off. That is, if hole images appear off, it is not the image shift of "hl" preset that needs correcting but that of "sq" preset.**

Solution:

-   Pause before next hole or square by clicking Hole/Toolbar>Pause button or Square/Toolbar>Pause button, respectively. Which one to pause depends on what is the next target.


-   Center the grid at a location that can be recognized by either:
     
    1.  Move to the alignment position:
         
        (It may be necessary to adjust the position at the scope after this since the goniometer can not move back to a position as accurately as we need it).
         
        -   Leginon/Navigation/Stage Location> Choose the name for the stored alignment position ("align" if you have been following the setup check list). and send it "To Scope"
             
    2.  scope> move the specimen to a position on the same square, either on a recognizable object or burn a good hole through ice as preparation for lower mag preset image shift correction

Perform [Preset Image Shift Alignment](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Medium-mag-preset-image-and_beam-shift-refinement)

Still not working: You may have an invalid combination of settings such as using [Iterative Stage Movement](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Iterative_Stage_Movement) while [queuing up](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Queuing_option) targets on the images so obtained.

Solution:

-   Resolve the conflict.

## Targeting is consistently off in opposite direction from where you pick

Commonly Why: Camera configuration is different in calibration and now.

1.  All your targeting would be wrong. "Abort" target processing in the Target Watcher of "squares" and "holes".
     
2.  If you use the Tietz camera: scope/Leginon/Instrument/Camera> check your camera configuration. mirror should be ['vertical']. Change it if not, and "Set" the configuration.
     
3.  If you use the Gatan camera: scope/Digital Micrograph> check your camera configuration.
     
4.  Leginon/Presets Manager> send "sq" or "grid" "To Scope"
     
5.  Leginon/Navigation> "Acquire" an image with "Use this configuration" Unchecked in the Camera Configuration.
     
6.  Leginon/Navigation> "Navigate" by "Image Shift", "Beam Shift", or "Stage Position" to center on a reference object or burn mark made in the high mag presets. This is to check if it behaves correctly now.
     
7.  Select targets again, or, if atlas is wrong, republish the target list to make the atlas.

## Hole targeting is inconsistently off or goes bad in the next run after correction

Commonly Why: Not well understood but may be related to microscopy alignment and settings such as normalization of lenses. up to 1.5 um error has been observed even with a reasonable calibration. The following solutions only works some times.

1.  Leginon/Drift Manager>"Declare Drift" to force correction for possible drift.
     
2.  Repeat image shift correction alignment [as in the case when targeting is consistently off](/leginon/Leginon_Manual/Trouble_shooting/Troubles_with_Targeting#Targeting_is_consistently_off_in_the_same_direction_and_distance).
     
3.  Ignore the first targetted '"hole" in the "squares" image. The second and on are more consistent when there is a hysteresis problem.
     
4.  Repeat ["Mag Only" Modeled Stage Calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Modeled_Stage_Position_calibration) at the "square" preset.

## Hole targeting is off more when the image shift target is away from the center of the image

Commonly Why: caused by different reference space mapping at the lower/high mag.

Solution: Get better estimate of the high mag stage position calibration by [Scaling Image Shift Matrix Calibration](/leginon/Scaling_Image_Shift_Matrix_Calibration)

## Automatic hole finding fails to pick up good ice thickness after set up

Commonly Why:

-   Electron beam intensity has changed


-   Blob threshold is not inclusive enough to tolerate variations


-   Ice contaimination

Solutions

-   Monitor electron beam with a saved location with an empty hole in navigator and check the recorded intensity periodically and adjust zero ice thickness accordingly.


-   Reduce Blob threshold in Alias nodes of the Hole Finder.


-   Make sure the anticontamination cryo box is properly inserted on the scope.


-   Remove the film camera from the scope if you don't need film.

## No broken grid square for dose measurement and ZLP alignment for MSI-Tomography

Solution

-   Burn a hole clear of ice and pick it as the reference target in "Hole Targeting" or "Tomography Targeting"

[< Troubles with Imaging](/leginon/Leginon_Manual/Trouble_shooting/Troubles_with_Imaging_-_Troubleshooting) | [Troubles with Focusing and Drift Check >](/leginon/Leginon_Manual/Trouble_shooting/Troubles_with_Focusing_and_Drift_Check)
