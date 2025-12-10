This checklist is valid for users needing the full leginon capacity such as those of MSI application. "Manual" application users can set up the microscope in Low Dose Mode and follow their usual practice. The list in practical order includes alignments that are critical for Leginon operation and are ones Leginon can not perform, yet. Other alignments not mentioned here can often be refined within leginon. Conditions listed in [] show possible ways to check the alignment. In most cases, alignment is only needed if the check fails. * indicates tips for better results

-   Check that Low Dose Mode is NOT activated


-   Adjust the grid to eucentric height using the Alpha Wobbler in HM mode


-   Reset to Gaussian focus at eucentric height to provide a good starting point for alignment in both HM and LM mode
    *At LM mode, Gaussian focus can be reached by adjusting the image to the point of contrast reversal with the defocus knob. A halo-type effect is also produced around the image (when the beam radius is small) at defocus values away from true focus.


-   Gun Alignments [Bright point at the center of the lightly defocused, large "spot size" beam. Bright and Coherent Beam]
    *Load a previous alignment for a better starting point.
    ITERATE
    -   Condensor aperture centering
    -   Condensor stigmation
    -   Gun tilt
    -   Gun shift
    -   Gun tilt pivot point (if tilt and shift are hard to optimize)
    -   Spot size dependent gun shift (if the beam jumps a lot between spots)


-   HM Beam Alignment (iterate) [image and beam do not move with change of defocus]
-   Check eucenter and reset to Eucentric focus again
-   Perform this alignment at 200k+ x may increase the accuracy although doing it at the mag where the autofocus is performed (usually 50k x) reduces variation from day to day.
-   ~~Do not click on the "Beam Shift" option in the direct alignment page in Tecnai UI. It resets the beam shift value, and do more harm than good if you want to import presets from other days.~~
-   **Revised**: For FEI Krios/Arctica/Talos: Use "Beam Shift" option in the direct alignment page to reset the beam shift to the center of the camera at the size of the beam you will use if you would like to use 0,0 beam shift at your final exposure presets.

ITERATE

-   For the following alignments, it is best to use Leginon to estimate the Z-focus. Go to the Z-focus node and click on the "simulate target" icon. Also, it is important to be at Zero Focus (eucentric focus). Use the manual focuser in Leginon to make sure that you are at eucentric focus before performing these alignments.
    -   Beam tilt pivot point x
    -   Beam tilt pivot point y
    -   Rotation center (i.e. set proper beam tilt)


-   HM Image/Beam Calibration [image does not move when beam is shifted and vice versa]
    *Available on FEI Tecnai series only
    *For Alignment, follow instruction in Alignment/Image HM TEM/"Image/Beam Calibration"


-   In Diffraction Mode in HM range, center the objective aperture.


-   Objective lens stigmation correction in HM mode [isotropic Thon ring in FFT]

The followings are optional alignment in LM mode. The alignment is needed only if serious problems are found and the alignment in general won't ever converge as nicely as those in HM mode.

-   LM Beam Alignment (iterate) [image and beam do not move with change of defocus]
    *Reset to Eucentric focus again for best result
    *Perform this alignment at one of the higher mags or at the mag for "sq" preset in MSI application is recommended
    -   Beam tilt pivot point x
    -   Beam tilt pivot point y
    -   Rotation center (i.e. set proper beam tilt)


-   LM Image/Beam Calibration [image does not move when beam is shifted and vice versa]
    *Available on FEI Tecnai series only
    *For Alignment, follow instruction in Alignment/Image LM/"Image/Beam Calibration"


-   Diffraction lens stigmation correction in LM mode [isotropic details at the edge of a hole]

[< Good Alignments Save Time](/leginon/Leginon_Manual/Instrument_Set-up/Good_Alignments_Save_Time) | [Microscope Set-up ^](/leginon/Microscope_Set-up)
