## Focuser and drift manager toggle back and forth forever

Commonly Why: Threshold set in focuser/autofocus is significantly smaller than that in drift manager in absolute scale. This is a bug in Leginon to some extend caused by a small movement of the image when the a new state of the beam is set so that the focuser records bigger drift than the drift manager.

Solution: Increase Focuser/Autofocus Drift Threshold and/or increase the wait time between checking drift in Drift Manager.

Still not working: Despike might not work in the corrector

Solution: Consider increasing Despike neighbor size (odd number only) or decreasing despike threshold.

Still not working: You are on a day with a lot of cosmic events that cause the cross correlation fails.

Solution: Finding a way to reduce exposure time might help as it reduces the possibility of cosmic ray hitting the CCD.

## Failed autofocus in Focus node

Commonly Why:

-   The actual defocus is outside of measurable range.


-   No image contrast for correlation due to thick ice, no ice and support film, or at Gaussian focus


-   Stage drift, charging, or ice melts during the focus measurement. All three cause change in images not accountable by beam tilt induced image shift.


-   Artifacts in the images such as spikes not corrected by the corrector node that fool the correlation procedure to consider the image is never moved or moved a lot.


-   Bad rotaion center and beam tilt pivot point alignment


-   Objective aperture is off alignment.


-   Bad calibration

Solutions:

-   Out of range:
     
    -   Make sure that the lower mag autofocus, i.e., Z focus node, is preformed successfully by observing its progress, and, if necessary, adjust the stage height in its Manual focus tool.
         
    -   Make sure that Z Focus node autofocus accuracy is compatible with the Focus node. For example, Z Focus at 5000x has an accuracy of [/- 5 um and Focus at 50,000x can handle range up to about]{.underline}/- 10 um.
         
    -   Choose a flater grid square.


-   For thick ice
     
    -   Leginon/Focus/Settings/Autofocus> Increase the ice melt time in autofocus setting
         
    -   Leginon/Exposure Targeting/Hole Targeting Setting/Target Template/Focus Template Thickness> Adjust allowed ice thickness values to pick focus target in area with thinner ice
         
    -   Leginon/Presets Manager> reduce "fa" preset CCD binning and/or increase exposure time.
         
    -   Bad rotaion center and beam tilt pivot point alignment
         
    -   Bad calibration


-   For stage drift during the procedure
     
    -   Leginon/Focus/Settings/Autofocus> Reduce drift check threshold.


-   For charging during the procedure
     
    -   Leginon/Exposure Targeting> Pick targets away from ice chunk, grid bar, and large ice gradient.


-   For ice melting during the procedure
     
    -   Leginon/Focus/Settings/Autofocus> Increase ice melt time


-   For image spikes
     
    -   Leginon/Correction> Adjust despike parameters
         
    -   Leginon/Correction> Reduce exposure time? Might reduce number of random event

## Failed autofocus in Z Focus node

Commonly Why:

-   The stage height relative to Eucentric point is outside of measurable range due to very uneven grid or stage far away from U-center.


-   Empty area or area with very thick ice, or at Gaussian focus


-   Objective aperture is off alignment.


-   Bad recorded eucentric focus.


-   Bad rotaion center and beam tilt pivot point alignment


-   Bad calibration

To identify which is the source, observe the image, correlation, and peak during beam tilt autofocusing. Also check in the log the residual value (so called min) of the fitting.

-   Image has very good contrast but features are completely different from one tilt image to the next-Out of range.


-   No image contrast or correlation peaks move randomly-empty or thick ice, or at Gaussian focus


-   Contrast reverse in the holes relative to the support matrix in one or more beam tilt images-Objective aperture is off alignment.


-   If you know that the stage is at U-center, but the images appear to be strongly defocused-Recorded eucentric focus is incorrect.


-   Correlation peaks are well defined but fitting fails-Bad rotaion center and beam tilt pivot point alignment, or bad calibration.

Solutions:

-   Out of range:
     
    -   U-center the stage before the run and when Z focus fails.
         
    -   Activate Manual Check after autofocus to make adjustment in stage Z height.
         
    -   For expert user: Add another focus step before the current autofocus step at even lower magnification for a larger range usability. For example, use sq preset. You will need to perform a calibration with Beam Tilt node in the Calibration application.


-   Empty area or thick ice:
     
    -   Pick better focus target.
         
    -   Leginon/Z Focus/Hole Targeting Settings/Ice Thickness Threshold/Focus Hole Selection> Consider using "Good hole" rather than "Any hole".


-   At Guassian focus:
     
    -   There is no problem, don't worry.


-   Bad recorded eucentric focus
     
    1.  Leginon> send to scope the preset used to autofocus in Z Focus node (i.e., hl in MSI).
         
    2.  TEM> Adjust the stage to U-center.
         
    3.  TEM> Focus the image and reset defocus.
         
    4.  Leginon/Z Focus> start Manual focus tool.
         
    5.  Leginon/Z Focus/Manual Focus> send 0 defocus to scope.
         
    6.  Leginon/Z Focus/Manual Focus> save "Eucentric focus from Instrument".


-   Bad rotation center and beam tilt pivot point alignment:
     
    -   Make sure you are at the eucentric focus during the alignment.


-   Bad alignment on objective aperture:
     
    -   Center the objective aperture in diffraction mode.

## Objects reverse contrast during autofocus

In this case of autofocus failure, objects such as holes change from lighter than matrix to darker as if a dark-field image is collected during the autofocus beam tilts.

Commonly Why:

-   The objective aperture is off.


-   Bad rotation center and beam tilt pivot point alignment.

Solutions:

-   Align objective aperture at mags where autofocus is performed in HM mode. Here is how:
     
    1.  TEM>Make sure the rotation center is correct.
         
    2.  TEM>Change the mag to that of the autofocus preset that shows the problem.
         
        or
         
        Leginon/Presets Manager>Send the autofocus preset.
         
    3.  Imaging an area that have scattering matter such as with ice or carbon.
         
    4.  TEM>Press the diffraction button to go into diffraction mode.
         
    5.  TEM>Use the Mag adjustment knob to change diffraction distance to ~1 m.
         
    6.  TEM>You should see a bright and condensed image of your imaging area which would condenses to a point if you are right at focus (adjust with focus knob). The faint disk outside of the bright area defines the opening of the objective aperture. Center the image using the MULTIFUNCTION KNOBS if you can not see the
        edge. Move the STAGE to area with more scattering matter if the faint disk is not visible.
         
    7.  TEM>Physically move the aperture so the faint disk is centered on the bright image.

[< Troubles with Targeting](/leginon/Leginon_Manual/Trouble_shooting/Troubles_with_Targeting) | [Troubles with Calibrations >](/leginon/Leginon_Manual/Trouble_shooting/Troubles_with_Calibrations_-_Troubleshooting)
