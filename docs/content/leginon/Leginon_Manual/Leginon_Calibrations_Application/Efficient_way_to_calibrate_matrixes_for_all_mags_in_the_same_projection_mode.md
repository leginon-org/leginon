This instruction assumes that you are familiar with individual nodes that performs the calibration.

We Use K3 installed behind energy filter of G2 Krios as an example.

The magnification that are relavent are 2250x and above in SA mode.

We use 2250x mag in micro probe mode for "sq" mag and 81000x (~1.1 Å/physical pixel) and nano probe mode for en.

## Reset defocus at Eucentric focus at all relevent project and probe mode.

This instruction assumes that all your projection and probe mode are referencing the same focal point that has no rotation other than simple 90 or 180 rotation imposed by the microscope manufacturer. It is important to make sure it start off right.

1.  send each preset you plan to use, from low to high.
2.  presss eucentric focus button on the scope.
3.  reset defocus

## Pixel Size calibration

1.  Use the value already calibrated by Gatan Engineer or TIA value and enter for 81000x (Don't forget that this is entered as in super-res mode so it should be around 5.5e-11 m
2.  Extrapolate the pixel size to all magnifications.

## Matrix calibration

-   DO NOT ATTEMPT TO DO STAGE POSITION CALIBRATION AT your en preset.* Follow the following:

### If the scope has M mode, make rough calibration for all M mode magnification, assuming same image orientation.

1.  Send your lowest mag preset that is in M mode and then set the scope to eucentric focus.
2.  Calibrate image shift at this setting.
3.  Use the scaling tool in Matrix node to scale it to all higher mags.
4.  Calibrate stage position at the same low mag, eucentric focus settings.
5.  Scale it to all higher mags.

### Repeat the same in SA mode.

See [Scaling Stage Position Matrix](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Stage_Position_matrix_calibration/Scaling_Stage_Position_Matrix)

### Refine image-shift calibration by the high defocus used in your presets.

1.  Send your actual sq, hl preset with its specific high defocus to scope.
2.  Calibrate image shift at this setting.
3.  Try out the beam-image shift targeting from hl to en and see if this works well.

**We do not redo stage position calibration in the high-defocus presets in this protocol. It is probably better without that refinement for beam-image shift targeting**

## Rotation/Scale calibrations

If the above is not enough, you can apply additional rotation and scale. Do this on hl preset.
I still have not found good trick other than what is already stated.
See [Scale Rotation Node](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Apply_Extra_rotation)
