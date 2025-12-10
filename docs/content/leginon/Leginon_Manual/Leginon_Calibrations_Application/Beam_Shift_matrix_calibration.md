# DO NOT GO THROUGH THIS CALIBRATION ON JEOL SCOPES. DO [Image Beam Compensation calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Image_Beam_Compensation_Calibration) instead.

## This calibration requires concentrating the beam on a small area of the sensor. Do not attempt this on radiation-damage-sensitive DDD (Gatan K2, DE-12, DE-20, Falcon unless you have ways to reduce the beam intensity at the same magnification by using spot size that gives you week enough beam).

Beam shift matrix calibrations are used at each magnification that Leginon uses. These
calibrations are not absolutely necessary, but can be very helpful to center the beam in the
navigator node. In this case, *the image of a small beam within the CCD is treated as an object
in the image.* When the beam is shifted by the electromagnetic lenses of the microscope, the
imprint of the beam moves relative to the CCD. The 2x2 transformation matrix created then
relates the values sent to the microscope and the amount of "beam shift" movement seen on the
CCD imaging area. Only one set of measurement is sufficient for beam shift matrix
calibration.

[How does matrix calibration work?](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Image_Shift_matrix_calibration)

1.  Leginon/Presets Manager> Select a preset for the calibration and send its
    parameter to the microscope. Matrix calibration depends only on magnification and
    microscope high tension. Therefore, only one preset per combination needs to be
    calibrated.
     
2.  Scope> contract the beam sufficiently so that it remains in the area of CCD
    acquisition during the calibration. It is also preferable that the CCD is imaging an
    area with no distinct feature such as an empty grid square to minimize false peak from
    unmoved object during a beam shift. At low magnifications, stage can be pulled out and
    parked with a spacer to create the empty field.
     
3.  Leginon/NodeSelector> select "Matrix" node.
     
4.  Leginon/Matrix> the preset CCD configuration is almost certainly bad for imaging
    contracted beam. Therefore, DO NOT use "test acquire" at this point.
     
5.  Leginon/Matrix/Toolbar> open "settings" window by clicking the icon to select
    camera configuration and correlation method. The former will take into effect only if
    "Overwrite Preset" is checked. Click "OK" to save the settings and close the window when
    done.
     
    *Tip: 1024x1024 binned by 4 and a VERY short exposure time can save time but still
    keep the contracted beam from burning the CCD.
     
6.  Leginon/Matrix/Toolbar> left-click "Acquire Image" to obtain a test image with
    current parameters.
     
7.  Leginon/Matrix/Toolbar> select "beam shift" as the Parameter and open the
    "Parameter Setting" window by clicking on the icon to the right of the selector.
     
8.  Leginon/Matrix/Matrix Settings> "Average # position"=1 is sufficient. The rest
    can be left in default values. "Interval" is not a relavent parameter since " average #
    position"=1.
     
9.  Leginon/Matrix/Toolbar> left-click (Execute icon) to calibrate.
     
10. The image of the beam should be shifting 10-30% of the imaging area. If this is not
    the case, then adjust shift fraction so that this occurs. The images can be monitored in
    Image Display Panel with display selection in image control panel set to "image". The
    cross correlation and its peak can also be displayed. The beam need to be contained in
    the imaging area at all time.
     
11. Use Navigation node to [check the result of the calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Checking_Matrix_and_Modeled_Stage_Position_Calibration).

**Beam Shift Calibration Need for the Example MSI:**

  ------------- -------------------------------------------------------------------------------------
  **Preset**    **magnification**

  gr            120 (rarely used)

  sq            550 (rarely used)

  hl            5000 (seldom used)

                11000 (useful in beam shift alignment tool in Presets Manager to align the beam at
                50000x)

  fc,fa,en,ef   50000 (useful)
  ------------- -------------------------------------------------------------------------------------

*The Presets Manager beam shift alignment tool works best using ~5x lower magnification than the
preset meant to be aligned in order to see the whole beam in view. This means that for
fc,fa,en,ef that are at 50000x, a calibration at 11000x is required at the similar defocus
range.

[< Image Shift matrix calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Image_Shift_matrix_calibration) | [Stage Position matrix calibration >](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Stage_Position_matrix_calibration)
