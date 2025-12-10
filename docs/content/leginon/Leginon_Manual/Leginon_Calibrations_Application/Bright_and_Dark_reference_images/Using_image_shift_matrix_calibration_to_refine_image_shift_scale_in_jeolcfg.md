The image shift matrix is affected by the IMAGE_SHIFT_SCALE in jeol.cfg. Our initial jeol.cfg scale is rough. Therefore, the first round of image shift matrix calibration will likely fail the default 12% tolerance. We will have to perform iteration of scale adjustment in jeol.cfg and image shift matrix calibration until the values are right.

Note that this procedure relies on [correct pixel sizes](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Pixel_Size_Calibration). Make sure the low magnification range is well calibrated before this calibration/refinement.

## Follow [Image Shift matrix calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Image_Shift_matrix_calibration) at each magnification with the following change:

1.  Leginon/Matrix/Matrix Settings> Reduce the calibration shift percentage to ~ 10 % so that the beam does not move away.
2.  Leginon/Matrix/Matrix Settings> Increase the calibration tolerance as this is likely failed due to rough value in jeol.cfg SCALE values. 50 % is quite likely the value you need instead of the 12 % set in the default.

Examine the log message from a successful calibration. Each axis will have an output like this:

    Pixel size error: xx.xx% (pre pixel xxxxxx)
    Or config scale multiplication = 1.50

Multiple the corresponding IMAGE_SHIFT_SCALE_axis in jeol.cfg by the value.

## Close Leginon and Leginon Client and then restart them so that jeol.cfg is reloaded at the scope.

## Repeat the calibration in **Matrix** node. The multiplication factor should be much closer.

[< Bright and Dark reference images](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Bright_and_Dark_reference_images) | [JEOL scopes: Image Beam Compensation calibration )>](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Image_Beam_Compensation_Calibration)
