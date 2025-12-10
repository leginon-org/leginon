Leginon will not function if calibrations have not been done. In essence, this (or a
similar combination of nodes) is the first application that should be used if calibrations do
not already exist. The term calibrations is an inclusive term that refers to different sets of
measurements such as image shift and stage position.

Unless you plan to perform calibration to all available magnification and camera
configuration, the first step in performing calibration will be to [set up Presets](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Creating_Presets_for_the_first_time).

The following lists all the calibrations that must be completed for Leginon MSI
application to function correctly. Some calibrations can not be performed without existing
calibration of the others. Therefore, it is necessary to follow the order listed below for the
very first calibration for an empty database:

-   [Pixel size calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Pixel_Size_Calibration) (for all the magnifications
    that will be used)


-   [Bright and Dark reference images](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Bright_and_Dark_reference_images) (for all the image dimension and binning that will be used)


-   (Optional) [Beam Shift Matrix calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Beam_Shift_matrix_calibration) (for all the magnifications that will be used)


-   [Image Shift Matrix calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Image_Shift_matrix_calibration) (for all the magnifications that will be used)


-   [Stage Position Matrix calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Stage_Position_matrix_calibration) (for the
    magnifications that will be used for gr preset in MSI... e.g. 120x)


-   [Modeled Stage Position calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Modeled_Stage_Position_calibration) (for magnifications
    in the range of ~550x to 1100x that will be used for sq preset in MSI...e.g.
    550x)


-   [Beam Tilt Defocus calibrations](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Autofocus_Calibration_with_Beam_Tilt_Node) (for the magnifications
    focus will be corrected at, both for z and defocus correction. These are the hl and fa
    presets in MSI, respectively... e.g. 5000x and 50kx)


-   [Beam Tilt Stigmator calibrations](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Autofocus_Calibration_with_Beam_Tilt_Node) (for the
    magnifications where the focus and astigmatism will be corrected at. These are the hl
    and fa presets in MSI... e.g. 5000x, 50kx)


-   [Store eucentric focus value](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Autofocus_Calibration_with_Beam_Tilt_Node) (for the
    magnifications where the stage z will be used for defocus correction. The hl presets in
    MSI is typical... e.g. 5000x)


-   [Store rotation center beam tilt value](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Autofocus_Calibration_with_Beam_Tilt_Node) (for the
    autofocus magnifications where the image shift is used as move type in targeting if
    the stage is to be tilted. For example, the "fa" preset in MSI... e.g. 50000x)


-   [Dose (camera sensitivity) calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Dose_Camera_Sensitivity_Calibration) (for one
    magnification, the rest are scaled by the program automatically).

![](images/Cal_flow.png)

In most cases, calibration only needs to be done once. Through experience, we have found the Stage Position and Calibrations involving Beam Tilt need to be refined often. The other calibrations (in our experience) do not fluctuate as frequently as these two do. Modeled stage position calibration does gradually go off over several months and a full calibration of the modeled stage position matrix is required to rectify the problem.

Image Shift, Stage Position, and Modeled Stage Position matrix calibration are being completed so that targets can be accuratly centered in the images at each different magnification. At the lowest magnifications, an image shift is too big without inducing significant beam shift so the stage has to be moved. As the magnification increases, a simple
calibration of stage movement (error typically of 1.5 um or more) is not adequate, so we have to model the stage movement (error typically of 1 um or less), but still move the stage. At
even higher magnifications (e.g. hl, en, ef, fc, and fa) image shifts (error of 0.3 um or less) can be used to go to targets.

The following are magnifications and types of positioning calibrations that typically have
been completed at a very minimum:

Move Type Calibration Need for Presets in Example MSI:

  Magnification:                                         Calibrations:
  ------------------------------------------------------ -----------------------------------------------
  120 (i..e., mag for "gr" preset)                       modeled stage position(mag-only), image shift
  550 (i.e., mag for "sq" preset)                        modeled stage position(full), image shift
  5000 (i.e., mag for "hl" preset)                       image shift
  50000 (i,e, mag for "fa","fc","en" and "ef" presets)   image shift

The Presets Manager has a "Calibration Status" section that will show which calibrations
have been completed for the given mag the selected preset is set to. We usually calibrate for
a range of magnifications so that later we will not have to complete them.

[Grids for Calibration >](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Grids_for_Calibration)
