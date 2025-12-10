## Preset Design

Preset design includes the normal gr, sq, hl, fa, and fc presets as in MSI. "tomo" preset is the preset used to collect the final tomogram. "preview" is set at minimal dose to check the quality of the region before final acquisition. The table here is for FEI Tecnai F30. For F20, your may use standard MSI application presets with the addition of "tomo" and "preview" at the magnification apropriate to your specimen.

### Example Multiscale Tomography preset parameters (on FEI Tecnai F30)

  Magnification:   Preset name:   Image Shift (x,y):   Dimension:   Binning:   Beam Coverage:   Exposure Time (ms):   Spot Size:   Defocus (m):   Skip when cycling:
  ---------------- -------------- -------------------- ------------ ---------- ---------------- --------------------- ------------ -------------- --------------------
  220              gr             Aligned*            512          8          max              25                    8            --1e-3         no
  480              sq             Aligned*            1024         4          1x CCD size      125                   8            --1.5e-3       no
  4500             hl             Aligned*            1024         4          1x CCD           125                   8            --1.2e-5       no
  34000            fc             0,0                  1024         1          <~ 1x CCD      500                   8            --1e-5         no
  34000            fa             0,0                  1024         4          <~ 2x CCD      100                   8            --5e-6         no
  34000            tomo           0,0                  4096         1          >2x CCD         160                   8            --1e-5         no
  34000            preview        0,0                  1024         4          2x CCD           12 (0.25e/A^2)       8            --1.2e-5       no

*The image shift for these presets need to be aligned against one of the high mag preset such as "fa" or "tomo".

**Protocol from Lu Gan suggest activate "Skip when cycling for these LM presets" after all tomography targets are selected in "Tomography Targeting" node so that these presets are not used any more. The newer protocol by Jian Shi does not do so.

## Calibrations

This application has the same calibration requirement as MSI applications, no additional calibration is needed if the same magnification and camera configuration are used. The exception is that the Tomography node uses images acquired in the same node to make the off axis correction in the tilt axis. As the result, the calibration of the move type the Tomography node uses and at the magnification of "tomo" preset is required. Since we normally perform image-shift calibration for all magnifications, it should already be included.

### Additional calibration needed for the Example MSI-Tomography

  Preset   magnification   calibration type         optional calibration
  -------- --------------- ------------------------ ---------------------------------------------------------------------------------------------------------------
  tomo     34000           image shift matrix       stage position matrix or rotation and scale-only modeled stage position (if using tilt-corrected correlation)
  hl       4500            modeled stage position   

Again the calibration is required only once in most cases. See the chapter on [calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application) for more details.

## Preferences and Settings

The default settings loaded at installation should be reasonably good for the first trial. See the section on [MSI-Tomography preference settings](/leginon/Leginon_Manual/Preferences_Setup/MSI-Tomography_Preferences) in the chapter on initial MSI application preference setup.

[< Summary of this application](/leginon/Leginon_Manual/Leginon_MSI-Edge_Application/Summary_of_this_application) | [Running the application >](/leginon/Leginon_Manual/Leginon_MSI-Tomography_Application/Running_the_application)
