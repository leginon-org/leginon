Two functions have to be performed in Beam Tilt node to perform defocus and
z-height corrections used in autofocus procedures. Defocus calibration are
required for defocus correction. This plus a record of eucentric focus value are
required for the z-height correction to eucentric height.

**We have disabled Stigmator Calibration and Correction in 2.2 because it has not been useful**

Beam Tilt Defocus/Stigmator Calibration and Eucentric Focus Recording Need for the Example MSI:

  -------- ---------------
  Preset   magnification
  hl       5000
  fa       50000
  -------- ---------------

## Defocus Calibration

1.  Leginon/Presets Manager> send the preset you want to make the calibration "To Scope"
     
2.  Leginon/Beam Tilt/Toolbar/Setting> check and make sure that "Override Preset" is NOT checked
3.  Leginon/Beam Tilt/Toolbar> select Defocus as calibration type
     
4.  Leginon/Beam Tilt/Toolbar> open "Parameter Settings" window to set parameters as follows:
     
    at 50,000x: defocus1 = --2e-06, defocus2 = --4e-06 and beam tilt angle=0.01
     
    at 5,000x: defocus1 = --2e-05, defocus2 = --4e-05 and beam tilt angle=0.01
     
5.  Leginon/Beam Tilt/Toolbar> click Calibrate.
     
6.  Occasionally the beam may be partially blocked by the objective aperture and
    produce a dark field image upon beam tilts. Reducing the beam tilt angle, using a
    larger objective aperture, and/or centering the objective aperture accurately are the
    possible solutions.

## Checking the Calibrations

Once Defocus are calibrated against beam-tilt induced image shift,
the two can be measured using the Measure Function in the Toolbar.

1.  Leginon/Beam Tilt/Toolbar> click Measure to open measurement submenu.
     
2.  Leginon/Beam Tilt/Measure> click Measure (to test the beam tilt defocus calibration).
     
3.  Leginon/Beam Tilt/Measure> click Correct Defocus to make the correction according to the measurement.
     
4.  Leginon/Beam Tilt/Measure> click Reset Defocus and exit the sub-window.
     
5.  Leginon/Presets Managaer> send the fc preset "To Scope"
     
6.  Leginon/Focus/Settings> select fc as the preset used for the acquisition.
     
7.  Leginon/Focus/Toolbar> start Manual Focusing.
     
    Power Spectrum of the image at defocus specified by "fc" preset should appear on
    the screen.
     
8.  Leginon/Focus/Manual Focus> set 0 defocus to scope by selecting the movetype
    to "defocus" and the number entry in meter to "0" and then click "Set
    Instrument".
     
    The Thone ring should disappear as the defocus is changed to zero measured by Beam
    Tilt node. If not, recalibration of defocus may be needed.
     
9.  Leginon/Focus/ToolbarManual Focus> stop Manual Focusing by clicking the "stop" button.
     
10. Leginon/Beam Tilt/Toolbar> click Measure to open measurement sub-menu.
     
11. Leginon/Focus/Toolbar> start Manual Focusing and check to see if the
    correction makes bad stigmation better.
    If not, redo stigmation correction.

Trouble Shooting:

See [Optimizing Autofocus](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Optimizing_Autofocus) for some pictures and more detailed description.

-   The microscope must be well aligned. The most critical are beam tilt pivot point and rotation center, both should be aligned at eucentric focus. Please refer to [Microscope Set-up](/leginon/Microscope_Set-up) to align the microscope well.


-   Chose a beam tilt and defocus change that will give a 10-20% shift in the image.


-   The beam should cover the entire CCD imaging area.


-   Have an easily recognized object at the center of the image for easy correlation. Avoid uneven areas.


-   Watch the images movement. There should not be any contrast reversal or appearance of the edge of the beam in any image acquired. Contrast reversal is caused by misaligned objective aperture or by too large a beam tilt angle so that part of the beam is blocked by the aperture when tilted.


-   Check the correlation image and peak location to find out if the image contrast is too low for good correlations.

## Eucentric Focus Storage and Retrieval

Encentric Focus From/To Scope (From/To Scope icons) do what they indicate. The "from
Scope" function simply records the current absolute focus value at the scope.
Therefore,

1.  Scope> eucenter the grid and reset defocus at U-centric height at the required high tension and at a high mag where focusing is easier.
     
2.  Leginon/Presets Manager> select the preset that will perform z-focusing (i.e., hl). temporarily change its defocus to 0.0
     
3.  Leginon/Presets Manager> sent the preset "To Scope"
     
4.  Leginon/Beam Tilt> left-click the Encentric Focus From Scope icon to save the focus value.
     
5.  Leginon/Presets Manager> return the defocus value back to its original.

## Rotation Center Storage and Retrieval

Rotation Center From/To Scope (From/To Scope icons) do what they indicate. The "from Scope" function simply records the current beam tilt value at the scope. Therefore,

1.  Scope> Align the rotation center at a magnification and high tension where the value will be used.
     
2.  Leginon/Beam Tilt> left-click the Rotation Center From Scope icon to save the beam tilt value to Leginon database.

[< Checking Matrix and Modeled Stage Position Calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Checking_Matrix_and_Modeled_Stage_Position_Calibration) | [Dose (Camera Sensitivity) Calibration >](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Dose_Camera_Sensitivity_Calibration)
