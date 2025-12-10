Note: The following serves as a quick set-up guide for the MSI application and assumes you have set up Leginon before. Use default values unless otherwise specified. If you are choosing the hole and exposure targets manually, you can of course skip the part regarding setting up the hole finders.

1.  Important - [Align the microscope](/leginon/Microscope_Set-up)
     
2.  [Start Leginon](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Starting-Up) (typically done on a computer in the microscope room) and load "MSI" application
     
3.  In Presets Manager, [import presets](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Import-existing-presets) from a previous day.
     
4.  Go to a "sacrificial" intact square with both filled and empty holes by moving the stage on the scope and [save its position](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Save-the-alignment-and-empty-position-in-Leginon) in Navigation node. If there are no squares with empty holes then burn through a filled hole. This square will be used for aligning presets and to set the I0 value for assessing ice thickness when setting up the hole finders
     
5.  (Skip if already reset defocus to Eucentric focus for LM in 1) [Go to sq preset](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Reset-defocus-to-zero-at-eucentric-focus-in-LM-mode), find true focus at eucentric height, and set defocus to zero on the microscope if you have not done so.
     
6.  (Skip if already reset defocus to Eucentric focus for HM in 1)[Go to fa preset](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Reset-defocus-to-zero-at-eucentric-focus-in-HM-mode). At the microscope, set stage at eucentric height, find true focus, and set defocus to zero on the microscope
     
7.  At the microscope, check and correct, if necessary, beam tilt pivot points and rotation center for HM mode
     
8.  [Correct image shift for gr](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Grid-preset-image-shift-refinement) preset against hl preset
     
9.  (Skip if calibration is stable on this scope) Check modeled stage position matrix calibration for gr preset by navigate it in Navigation node. Within 10% error is satisfactory. If not, perform [mag-only modeled stage calibration](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Grid-preset-stage-position-refinement) at gr preset using "Calibration" application.
     
10. In Grid Targeting node, press Calculate Atlas, then Acquire. Atlas collection may take 10-20 min.
     
11. Go to a broken square and [save its position](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Save-the-alignment-and-empty-position-in-Leginon) in Navigation node. Alternatively, select a broken square target from the atlas, submit it to move to the position but submit no hole targets when prompted to terminate the sequence. If there is no broken square, a hole can be burned at high mag where there is no support film.
     
12. In Presets Manager and an exposure preset, [set dose](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Determine-the-proper-exposure-condition-for-exposure-presets) to 10e-/A^2 for exposure presets by balancing the beam intensity against the exposure time
     
13. [Update flat field correction for exposure presets](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Update-bright-and-dark-correction-images-for-exposure-presets) by going to Correction node and acquire bright and dark images using the following settings:
     
    -   Binning: 4096 x 1
         
    -   Exposure time: the value obtained from the previous step
         
    -   Images to average: 3
         
    -   Number of Channels: 1 (Use 2 if your computer memory can handle it)
         
14. In Navigation, [return to the intact square](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Retrieve-the-stored-alignment-or-empty-position-in-Leginon).
     
15. Swing in the objective aperture and center it in diffration mode at an exposure preset.
     
16. Return to imaging mode.
     
17. Remove objective lens hysteresis
     
    -   If you have spent a long time in steps 10 to 12 (more than 20 min.), you should leave the scope at this high mag preset for 30 minutes. This allows the lenses to warm up and Leginon to effectively correct for lens hysteresis. (For experienced users: You may set up the hole finders without perfect presets alignment during this time. However, do remember to set the microscope to a high magnification as soon as the test image acquisition is done so the warm up is not delayed)
         
    -   If you have performed steps 10 to 12 without delay, the hysteresis can mostly be removed by cycling through all presets several times. To do so, select an exposure preset in Presets Manager, send to scope. When it finishes, send the same preset again to the scope which ensures that all presets are cycled through. repeat the same process at least one more time.
         
18. FEI scopes: Send en exposure preset to scope and use Direct Alignment Tool to center the beam and reset user beam shift value by clicking the Done button.
19. [Align image shifts](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Medium-mag-preset-image-and-beam-shift-refinement) and beam shifts for the fa, fc, hl, and sq presets against the exposure preset or, if fa and exposures are at the same magnification, use fa as reference to align hl and sq presets image shifts.
     
20. At this point the user should not have to manually operate the microscope anymore and can run Leginon from a remote computer.
     
21. In both Hole Targeting and Exposure Targeting, click Settings and check Allow for user verification of picked holes and check that queuing is off.
     
22. In Z Focus node, in the focus sequence tool, enable the focus step "Manual_after"
     
23. In Square Targeting, find the intact square on the grid atlas and [submit it as a target](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_Operation#Select-Squares-on-the-atlas). The location of the square is easy to find using the current position marker on the atlas.
     
24. Check that targeting is good [+/- 5 um] and set up the hole-finder in [Hole Targeting](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Hole-Targeting-Set-up). Set I0 value from the average intensity of the empty hole. Make sure in Focus settings, Focus hole selection is set to Any Hole (or Good Hole if good holes are abundent) and then activate automatic hole finding option for future images.
     
25. In Hole Targeting, [submit an empty hole](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_Operation#Select-Holes-on-the-first-image-of-a-square) as an acquisition (green) target and a carbon supported area with a recognizable junk on it as a focus (blue) target.
     
26. [Check results of Z focusing](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Autofocus-Test) to ensure focuser calibration is good at hl preset. [+/- 5 um or better]
     
27. Check that targeting is good [+/- 1.5 um] and set up the hole-finder in [Exposure Targeting](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Exposure-Targeting-Set-up). Set I0 value from the average intensity of the empty hole and then activate automatic hole finding option for future images.
     
28. In Focus node, in the focus sequence tool, enable the focus step "Manual_after"
     
29. Submit a [focus target](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_Operation#Select-Holes-on-the-first-image-of-a-square) and an [acquisition target](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_Operation#Select-Holes-on-the-first-image-of-a-square) from Exposure Targeting node.
     
30. [Check results](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Autofocus-Test) of focusing to ensure focuser calibration is good [+/- 0.3 um or better]
     
31. Check that targeting is good [+/- 100 nm]
     
32. If everything checks out, turn off Manual_after step in Focus and Z Focus node, turn off user verification option in Hole Targeting and Exposure Targeting nodes, pick squares, and watch the data come in.
     

[< Special Operation Preference setup](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Special_Operation_Preference_setup) | [MSI set-up in more details >](/leginon/MSI_set-up_in_more_details)
