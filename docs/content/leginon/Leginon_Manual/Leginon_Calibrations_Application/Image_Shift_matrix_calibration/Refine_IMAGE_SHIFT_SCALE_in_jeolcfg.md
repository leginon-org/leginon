The initial values for IMAGE_SHIFT_SCALE in jeol.cfg are often rough since it is done manually with approximation. These values need to be refined to achieve good image-beam shift targeting.

For each magnification used for setting presets,

1.  Determine accurately the pixel size and save them using [Pixel Size](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Pixel_Size_Calibration) node. Determine this at the defocus that is used in preset. Do not just just rely on magnification extrapolation at low magnification, especially not when defocus is high, since the apparent magnification would be altered by the large defocus.
2.  While doing [image shift matrix calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Image_Shift_matrix_calibration) , use a large enough tolerance to cover possible deviation of IMAGE_SHIFT_SCALE (50-80% is some times necessary) and a small enough shift so you don't lose the beam.
3.  The logger information at each calibrating axis contains a line that says, for example
        Or config scale multiplication = 1.4

    
    This means that jeol.cfg IMAGE_SHIFT_SCALE at the said axis should be modified by multiplying the value in jeol.cfg with 1.4.
4.  Make the change in jeol.cfg in a text editor. This will be reloaded only if Leginon is restarted.

Repeat 2-4 to improve the scale untilt the multiplication factor shown is close to 1.00 (+/-0.02 can be achieved from our experience)
