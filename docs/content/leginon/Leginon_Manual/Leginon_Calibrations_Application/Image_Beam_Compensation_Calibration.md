# DO NOT GO THROUGH THIS CALIBRATION ON FEI SCOPES. DO [Beam Shift matrix calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Beam_Shift_matrix_calibration) instead.

This calibration is used to estimate the beam shift required to bring the beam back to the center when an image shift is applied to reach a target. It is saved as beam shift matrix and is only relevant to JEM microscopes. Such compensation is applied by microscope software with FEI scopes.

**Image shift matrix calibration is required before performing this calibration**

1.  Leginon/Presets Manager> Select a preset for the calibration and send its parameter to the microscope. Matrix calibration depends on the instruments, i.e., the scope and camera used, magnification and microscope high tension. Therefore, only one preset per combination needs to be calibrated.
2.  Scope> Lower the main screen. This calibration does not actually acquire digital camera images.
3.  Scope> contract the beam sufficiently so that the center of the beam can be located easily on the main screen.
4.  Leginon/NodeSelector> select "Image Beam Comp" node.
5.  Leginon/Image Beam Comp/Toolbar> open "settings" window by clicking the icon to change the amount of image shift applied during the calibration. Click "OK" to save the settings and close the window when done.
6.  Leginon/Image Beam Comp/Toolbar> left-click "Calibrate" to open the calibration dialog.
7.  Leginon/Image Beam Comp/Calibrate> Follow the instruction for each step. Left-click Done when you have perform what it asks you to do at each step.
8.  Leginon/Image Beam Comp/Calibrate> Click OK when all steps are completed and satisfied to save the calibration. Click Cancel otherwise.

Testing:

1.  Leginon/Presets Manager> Select the preset sent above for the calibration and send its parameters to microscope and camera.
2.  Use Navigation node to [check the result of the calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Checking_Matrix_and_Modeled_Stage_Position_Calibration). Select "Image Beam Shift" as the move type. Feature on the image should be shifted but the beam remains centered.

**Beam Shift Calibration Need for the Example MSI:**

  ------------- -------------------
  **Preset**    **magnification**
  hl            5000
  fc,fa,en,ef   50000
  ------------- -------------------

[< JEOL scopes: Image shift matrix calibration and jeol.cfg refinement](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Bright_and_Dark_reference_images/Using_image_shift_matrix_calibration_to_refine_image_shift_scale_in_jeolcfg) | [Stage Position matrix calibration >](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Stage_Position_matrix_calibration)
