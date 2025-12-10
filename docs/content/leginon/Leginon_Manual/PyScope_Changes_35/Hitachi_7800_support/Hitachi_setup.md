## [Save mag and imaging-mode-dependent focus offset](/leginon/Leginon_Manual/PyScope_Changes_35/Hitachi_7800_support/Hitachi_install/Setup_and_Calibration_for_hhtcfg_and_focus_offset)

## Leginon Calibration specifics

### Follow the general installation and Leginon setup manual until you run "Calibrations" application and finishes obtaining your [Bright and Dark reference images](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Bright_and_Dark_reference_images).

### Refining scales in hht.cfg

Unfortunately, Leginon's targeting relies on fairly good scale values in hht.cfg. If you have low confidence on these initial estimate, we recommend doing some iterations of the following:

1.  Calibrate [pixel size](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Pixel_Size_Calibration) more accurately at each magnification used, including lower magnification with the defocus that will be used in experiment.
2.  Iterate adjustment of COIL_PA_SCALE, COIL_IA_SCALE values in hht.cfg and recalibrate in Leginon.

### Hint:

Run hht_scalecalibrator.py to calibrate the scale using a cross-grating grid. You can copy individual results from the output hht_test.log to your hht.cfg to replace the old scales.

For critical magnification, you can add mag specific scale calibration. For example, the following defines the limiting scale of all LOWMAG imaging mode at (--7.5e-4,7.5e-4) except that the scale would be (--7.4e-4,7.4e-4)

    COIL_IA_200_SCALE%LOWMAG%X = -7.4e-4,7.4e-4
    COIL_IA_SCALE%LOWMAG%X = -7.5e-4,7.5e-4

### Image Beam Compensation calibration

Hitachi scopes do not have a high level function we can access through scripting to move image shift without affecting beam location. Therefore, any Leginon node that uses IMAGE SHIFT move type should be changed to BEAM-IMAGE SHIFT.

This affects calibration procedure in two ways:

-   Image Shift should be calibrated at smaller shift distance if the beam moves too much to affect correlation.
-   [Image Beam Compensation Calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Image_Beam_Compensation_Calibration) at mid and high mags (i.e. mags for hl and fa,fc,en,ef) is required to perform the compensation

### Modeled Stage Position calibration

We have observed that HT7800 stage targeting works well only if using modeled stage position as the mover. Follow [Modeled Stage Position calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Modeled_Stage_Position_calibration) to do the calibration.

-   Number of periodical terms can be set to 0, and the number of data points in the calibration as few as 5 for it to work. We think the improvement comes from non-orthogonal stage axes that is not accounted for in simple matrix calibration.
