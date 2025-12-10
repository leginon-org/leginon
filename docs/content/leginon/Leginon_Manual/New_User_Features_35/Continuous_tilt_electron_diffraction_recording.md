Micro-ED involves recording 3D crystal electron diffraction pattern during a continuous stage tilt. Leginon implementation of this application includes the listed components below and is available by using myami-beta branch and myami-3.5 and above. As is, it is only fully implemented for TFS Ceta or Ceta-D camera.

Since many of the feature required here are not available through Standard or Advanced TEM Scripting from TFS, AutoIt scripts are used in several places.

## Components of the feature

1.  Diffraction mode TEM instrument
2.  Beamstop control: achieved by AutoIt Scripts BeamstopIn and BeamstopOut
3.  Rolling-shutter movie acquisition using TIA interface
4.  [Data conversion](/leginon/Leginon_Manual/New_User_Features_35/Continuous_tilt_electron_diffraction_recording/TIA_raw_data_conversion) and upload of the movies into Leginon database and crystallography format
5.  [MSI-Diffr application](/leginon/Leginon_Manual/New_User_Features_35/Continuous_tilt_electron_diffraction_recording/_MSI-Diffr_application_)
6.  [Camera length calibration](/leginon/Leginon_Manual/Camera_length_calibration)

## Installation (assuming that you've already have Leginon installation).

1.  Check that you have access to Advanced TEM Scripting (frame-saving upgrade not needed).
2.  Install or set environment to use git branch myami-3.5 and up or the current myami-beta on TFS microscope with Ceta camera as well as your leginon linux box and webserver for myamiweb.
3.  import updated Calibrations application (see [Steps involved in the installation](/leginon/Leginon_Manual/Administration_Tools/Steps_involved_in_the_installation))
4.  import MSI-diffraction and settings from your_myami/leginon/applications (see general description of [Steps involved in the installation](/leginon/Leginon_Manual/Administration_Tools/Steps_involved_in_the_installation) regarding importing application and additional settings for the application)
5.  [Setup Diffraction mode TEM instrument](/leginon/Leginon_Manual/New_User_Features_35/Continuous_tilt_electron_diffraction_recording/Setup_Diffraction_mode_TEM_instrument)
6.  [Setup Ceta to use Advanced TEM Scripting](/leginon/Leginon_Manual/New_User_Features_35/Continuous_tilt_electron_diffraction_recording/Setup_Ceta_to_use_Advanced_TEM_Scripting)
7.  [AutoIt program and script compilation](/leginon/Leginon_Manual/New_User_Features_35/Continuous_tilt_electron_diffraction_recording/AutoIt_program_and_script_compilation)
8.  [Setup movie upload with diffrtransfer.py](/leginon/Leginon_Manual/New_User_Features_35/Continuous_tilt_electron_diffraction_recording/Setup_movie_upload_with_diffrtransferpy)

-   On scopes that has both Falcon and Ceta, and the former is used for typical imaging, we create instruction for diffraction users to replace instruments.cfg with the one specific for diffraction work during their operation and then have them change it back afterward.

## Microscope optical settings

-   Gun Lens: 7.1 is the typical we use. This delievers about 1/4 of the beam intensity of Gun Lens 3.3 on Glacios
    -   We do not retake Gain reference at such high Gun Lens value. The beam is weak in imaging mode in this case and does not give the right gain reference for the diffraction peaks.
-   C2 Aperture: 20 um for any SA and diffraction presets. 150 um, or what you typically use that does not block the beam for grid atlas
-   Probe mode: nano probe parallel illumination whereever possible

## Presets unique for this application (Glacios with CetaD and 0.9 Å resolution)

  ------------- -------------- ------------------------------ ---------- ----------- -----------------------------------------------------------------------------------------------------------------------
  preset name   TEM            magnification(camera length)   SpotSize   Parallel?   Notes
  hl            Glacios        8500                           10         No          Minimize exposure dose is important since this preset is used for all target tracking and eucentric height adjustment
  df            DiffrGlacios   1100                           10         Yes         Exposure time is only relevant for Diffraction node where single acquistion is taken
  ------------- -------------- ------------------------------ ---------- ----------- -----------------------------------------------------------------------------------------------------------------------

## Calibration

1.  [Camera length calibration](/leginon/Leginon_Manual/Camera_length_calibration)

## Usage

### Check these before you start:

1.  Confirm that instruments.cfg is properly set up to use feicam for Ceta camera. **Falcon camera and Ceta camera can not both be loaded through feicam in instruments.cfg**
2.  Set gun lens value. This must be done manually. Use "Free control" option if needed.
3.  Open TUI. Select and insert BM-Ceta in the camera tab. Confirm that tui_acquire.au3 validation items are set [correctly](/leginon/Leginon_Manual/New_User_Features_35/Continuous_tilt_electron_diffraction_recording/AutoIt_program_and_script_compilation#TUIAcquire-Testing).
4.  Make sure TIA window is available and the Export Series shortcut is shown as required by [TiaExportSeries.au3](/leginon/Leginon_Manual/New_User_Features_35/Continuous_tilt_electron_diffraction_recording/AutoIt_program_and_script_compilation#TiaExportSeries-Testing)

### Start MSI-DIffr application and assign client as required.

### [Setup df preset](/leginon/Leginon_Manual/New_User_Features_35/Continuous_tilt_electron_diffraction_recording/Setup_df_preset)

### Grid atlas collection

1. Select gr preset to scope, with flucam showing the grid and aperture, draw on the computer screen the location of the centerred small C2 aperture.
2. Select a larger C2 aperture for grid atlas collection.
3. collect grid atlas.
4. Reselect the small C2 aperture. Make sure it is still centered.

### Queue up potential crystals

1. Pick square and then pick "hole" for intermediate mag image of potential crystals. (This is no different from any other MSI application).
2. Submit preview targets in "DExposure Targeting" node for a small rotation image and confirm whether it diffracts or not.
3. Submit the good crystal positions as acquisition targets into the queue in "DExposure Targeting" node. No focus target is needed.
4. If needed, modify "DExposure" settings for start, range, and speed of the tilt.
5. Click "process queue" tool to start collection

#### Important: Do not use "simulate target" tool directly in "DExposure" node. It needs a real target id to keep the tilt series saved unique and for diffrtransfer.py to function.

### Diffraction series naming convension

The diffraction series is named after the parent image database id and target number in its target list. For example, 123456_1
