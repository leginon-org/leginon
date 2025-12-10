Image shift matrix calibrations are used at each magnification that Leginon uses. All 2x2
matrix calibrations covered by the "Matrix" node works in the same way. For a particular type
of movement, in this case an "image shift" using the electromagnetic lenses of the microscope,
a 2x2 transformation matrix needs to be created that relates the values sent to the microscope
and the amount of "image shift" movement seen on the digital camera imaging area. Only one set of
measurement is sufficient for image shift matrix calibration.

## Image Shift matrix calibration on JEOL microscope is also used for iteratively [refine IMAGE SHIFT SCALE in jeol.cfg](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Image_Shift_matrix_calibration/Refine_IMAGE_SHIFT_SCALE_in_jeolcfg)

*How does matrix calibration work?*

> Matrix calibration is made by making N sets of measurements (specified by "N
> Average"). Each measurement set acquires three images, first at a given origin, second
> with an x-axis movement in the specified "Parameter" by the specified "Shift Fraction" of
> the image, and third with an y-axis movement by the same shift fraction. The resulting
> shifts in the acquired images are obtained by cross correlation. A transformation matrix
> is then generated for the measurement set. The origin is shifted by the "Interval"
> specified in the node, in meters before the next set of measurements is taken. At the end,
> the N matrixes obtained are averaged and saved in the database at the specific
> magnification and movement type and can be applied to any camera configuration.
> "Tolerance", expressed in fraction of image, is used as an error check. The calibration is
> considered failed when the measured movement is much different from that calculated from
> pixel calibration

1.  Leginon/Presets Manager> Select a preset for the calibration and send its
    parameter to the microscope. Matrix calibration depends only on magnification and
    microscope high tension. Therefore, only one preset per combination needs to be
    calibrated.
     
2.  Scope> Make sure that the digital camera is imaging an area with distinct feature.
    preferable isotropic, i.e., a single line is not appropriate but lines crossing each
    other is good.
     
3.  Leginon/NodeSelector> select "Matrix" node.
     
4.  Leginon/Matrix/Toolbar> left-click "acquire image" to obtain a test image with
    current parameters.
     
5.  If the camera settings are not ideal-
     
    Leginon/Presets Manager> If you have presets set up, you can change the camera
    setting of the preset and send it to scope.
     
    OR
     
    Leginon/Matrix/Toolbar> open "settings" window by clicking the icon to select
    camera configuration and correlation method. The former will take into effect only if
    "Overwrite Preset" is checked. Click "OK" to save the settings and close the window when
    done.
     
    *Tip: Use this step to set the camera configuration to 512x512 binned by 8 (and a
    short exposure time, of course) for presets with larger dimension and lower bin can save
    a lot of image acquisition time during the calibration.
     
6.  Leginon/Matrix/Settings> select correlation method. Phase correlation is
    especially efficient in cases where periodic pattern exist. The pattern often causes
    cross correlation peak search to misidentify the correct peak in the multiple peak
    correlation map.
     
7.  Leginon/Matrix/Toolbar> select "image shift" as the Parameter and open the
    "Parameter Setting" window by clicking on the icon to the right of the selector.
     
8.  Leginon/Matrix/Matrix Settings> "Average # position"=1 is sufficient. The rest
    can be left in default values. "Interval" is not a relavent parameter since " average #
    position"=1.
     
9.  Leginon/Matrix/Toolbar> left-click (Execute icon) to calibrate.
     
10. The image should be shifting 10-30% of the imaging area. If this is not the case,
    then adjust the shift fraction so that this occurs. The images can be monitored in Image
    Display Panel with display selection in image control panel set to "image". The beam
    should also be covering the entire imaging area at all time. If significant beam shift
    is produced during the calibration, then the microscope alignments need to be adjusted,
    especially image/beam calibration through the FEI software).
     
11. Use Navigation node to [check the result of the calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Checking_Matrix_and_Modeled_Stage_Position_Calibration)

**Image Shift Matrix calibration need for the Example MSI:**

  ------------- -------------------
  **Preset**    **magnification**
  gr            120
  sq            550
  hl            5000
  fc,fa,en,ef   50000
  ------------- -------------------

> **Note:** See [Scaling Image Shift Matrix Calibration](/leginon/Scaling_Image_Shift_Matrix_Calibration)

[< Bright and Dark reference images](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Bright_and_Dark_reference_images) | [Image Beam Compensation calibration (JEOL scopes)>](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Image_Beam_Compensation_Calibration)
