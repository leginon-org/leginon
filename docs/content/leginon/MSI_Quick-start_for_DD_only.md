This is a new version of MSI Quick-start based on Anchi's current recommendation for using Leginon at NRAMM on a scope where this is regularly done. The Leginon "culture" makes the alignment of the scope stable so that you can setup faster.

The example here assumes the use of only Gatan K2 Summit in Counted mode. See NRAMM [Preset design for Gatan K2 summit camera](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Pre-MSI_Set-up#Preset-Design-Example-for-small-pixel-Gatan-K2-camera-alone) for special presets used here.

1.  Start DM, make sure camera has cooled down and is healthy.
2.  Update Hardware Dark Reference in DM.
3.  Load a standard setup grid in the microscope such as a negatively stained grid with carbon support that will help you focus
4.  [Start Leginon](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Starting-Up) (typically done on a computer in the microscope room) and load "MSI" application
     
5.  In Presets Manager, [import presets](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Import-existing-presets) from a previous day.
     

## Start off scope alignment well with resetting defocus roughly to eucentric focus.

1.  Send "sq" preset to microscope and move to a "sacrificial" intact square with intact carbon support with scope stage control of the scope.
2.  Use microscope stage wobbler to get the grid roughly to eucentric height.
3.  [save its position](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Save-the-alignment-and-empty-position-in-Leginon) in Navigation node.
4.  Roughly [find and reset eucentric focus as defocus zero](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Reset-defocus-to-zero-at-eucentric-focus-in-HM-mode).

## Align the microscope gun and condenser system assisted by the presets

1.  Go to a broken square and [save its position](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Save-the-alignment-and-empty-position-in-Leginon) in Navigation node. Alternatively, select a broken square target from the atlas, submit it to move to the position but submit no hole targets when prompted to terminate the sequence. If there is no broken square, a hole can be burned at high mag where there is no support film.
2.  Check your final exposure dose rate to confirm that the electron beam intensity is similar to previous run. If so, gun alignment refinement should be minimal.
3.  Check the gun tilt/shift and condenser aperture centering and condenser lens stigmation at your final exposure preset, "ed" for example.

## Accurately align the beam tilt pivot points and rotation center for HM mode at the eucentric focus

1.  [return to the intact square](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Retrieve-the-stored-alignment-or-empty-position-in-Leginon).
2.  Accurately [find and reset eucentric focus as defocus zero](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Reset-defocus-to-zero-at-eucentric-focus-in-HM-mode).
3.  At the microscope, check and correct, if necessary, beam tilt pivot points and rotation center for HM mode

## Grid preset image shift alignment with HM preset

1.  Remove the objective aperture
2.  [Switch to larger condenser aperture for "gr" preset](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Condenser-aperture-2-switching-for-gr-preset) alignment
3.  [Correct image shift for gr](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Grid-preset-image-shift-refinement) preset against hl preset

# *You are now ready to put in your real grid for data collection*.

## Starts here if you are exchanging grid

## Adjust the grid roughly to eucentric height

1.  Find an open area using "gr" and then "sq" preset.
2.  Use microscope stage wobbler to get the grid roughly to eucentric height.

## Grid Atlas

1.  Remove the objective aperture
2.  [Change the second condenser aperture](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Condenser-aperture-2-switching-for-gr-preset) to that for "gr" preset
3.  Remove the objective aperture
4.  In Grid Targeting node, press Calculate Atlas, then Acquire. [Atlas collection](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Acquire mosaic atlas of the grid) may take 10-15 min.
     

## setup for MSI starting at viewing grid square

1.  Go to a broken square and [save its position](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Save-the-alignment-and-empty-position-in-Leginon) in Navigation node. Alternatively, select a broken square target from the atlas, submit it to move to the position but submit no hole targets when prompted to terminate the sequence. If there is no broken square, a hole can be burned at high mag where there is no support film.
     
2.  In Presets Manager and an exposure preset, [MSI set-up in more details#Adjusting the beam diameter of the presets for DD camera by its dose limit per frame exposure](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Adjusting the beam diameter of the presets for DD camera by its dose limit per frame exposure).
     
3.  [Update flat field correction for exposure presets](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Update-bright-and-dark-correction-images-for-exposure-presets) by going to Correction node and acquire bright and dark images using the following settings:
     
    -   Binning: full camera dimension with binning of 1
         
    -   Exposure time: the intended "ed" preset exposure time
         
    -   Images to average: normally 20 (all bright and dark if using analog DD (i.e., DE or bright images for counted/superres K2) See individual camera usage for more details.
         
    -   Number of Channels: 1 (Use 2 if your computer memory can handle it)
         
4.  In Navigation, [return to the intact square](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Retrieve-the-stored-alignment-or-empty-position-in-Leginon).
     
5.  Swing in the objective aperture and center it in diffration mode at an exposure preset.
     
6.  Return to imaging mode.
     
7.  Remove objective lens hysteresis
    -   If you have performed steps involving "gr" preset without delay, the hysteresis can mostly be removed by cycling through all presets several times. To do so, select an exposure preset in Presets Manager, send to scope. When it finishes, send the same preset again to the scope which ensures that all presets are cycled through. repeat the same process at least one more time.


1.  [Align image shifts](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Medium-mag-preset-image-shift-alignment) and beam shifts for the fa, fc, hl, and sq presets against the exposure preset or, if fa and exposures are at the same magnification, use fa as reference to align hl and sq presets image shifts.
     
2.  At this point the user should not have to manually operate the microscope anymore and can run Leginon from a remote computer.
     
3.  In both Hole Targeting and Exposure Targeting, click Settings and check Allow for user verification of picked holes and check that queuing is off.
     
4.  In Z Focus node, in the focus sequence tool, enable the focus step "Manual_after"
     
5.  In Square Targeting, find the intact square on the grid atlas and [submit it as a target](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_Operation#Select-Squares-on-the-atlas). The location of the square is easy to find using the current position marker on the atlas.
     
6.  Check that targeting is good [+/- 5 um] and set up the hole-finder in [Hole Targeting](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Hole-Targeting-Set-up). Set I0 value from the average intensity of the empty hole. Make sure in Focus settings, Focus hole selection is set to Any Hole (or Good Hole if good holes are abundent) and then activate automatic hole finding option for future images.
     
7.  In Hole Targeting, [submit an empty hole](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_Operation#Select-Holes-on-the-first-image-of-a-square) as an acquisition (green) target and a carbon supported area with a recognizable junk on it as a focus (blue) target.
     
8.  [Check results of Z focusing](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Autofocus-Test) to ensure focuser calibration is good at hl preset. [+/- 5 um or better]
     
9.  Check that targeting is good [+/- 1.5 um] and set up the hole-finder in [Exposure Targeting](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Exposure-Targeting-Set-up). Set I0 value from the average intensity of the empty hole and then activate automatic hole finding option for future images.
     
10. In Focus node, in the focus sequence tool, enable the focus step "Manual_after"
     
11. Submit a [focus target](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_Operation#Select-Holes-on-the-first-image-of-a-square) and an [acquisition target](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_Operation#Select-Holes-on-the-first-image-of-a-square) from Exposure Targeting node.
     
12. [Check results](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Autofocus-Test) of focusing to ensure focuser calibration is good [+/- 0.3 um or better]
     
13. Check that targeting is good [+/- 100 nm]
     
14. If everything checks out, turn off Manual_after step in Focus and Z Focus node, turn off user verification option in Hole Targeting and Exposure Targeting nodes, pick squares, and watch the data come in.
     

[< Special Operation Preference setup](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Special_Operation_Preference_setup) | [MSI set-up in more details >](/leginon/MSI_set-up_in_more_details)
