MSI-Diffr application is designed for electron diffraction data collection workflow. It is similar to other MSI workflow except the following nodes

## DExposure Targeting

This node is of JAHCFinder class. It is set not to require focus target, and to skip the automatic hole finding. The targets are sent to a queue. Only preview and acquisition targets are processed down stream from here.

## DPreview

This node is of MoveAlphaAcquisition class. It is set to process preview targets. The default behavior acquires a 5 second exposure image in the diffraction mode while the grid is tilted by ~5 degrees. The target is reached by stage position movement. The default does not do iterative navigator move so the targeting may not best but will ensure lowest radiation damage in this preview process.

## DExposure

This node is of DiffrFocuser class. It is set to process acquisition targets. The steps this node performs are

1.  move to the desired target with iterative navigation stage position movement
2.  follow the focus sequence to set the stage to eucentric at this position so that it is less likely to miss the crystal as it tilts. The images are taken in hl preset.
3.  set scope to df preset in Diffraction mode
4.  insert beam stop (AutoIt Script BeamstopIn)
5.  set the stage tilt to the start tilt and starts tilting
6.  close previous movie tab in TIA gui to avoid overloading the memory
7.  AutoItScript TuiAcquire do the followings in a separate thread;
    1.  Set and check TUI Camera interface to match the required parameters for rolling shutter movie acquisition.
    2.  Click the Acquire button to start movie collection
8.  When the tilting is completed, AutoItScript TuiAcquire clicks the Acquire button again to stop the movie recording.
9.  AutoItScript TiaExportSeries exports the movie series in binary format with name according to the parent image id and target number.
10. Stage is tilted back to the original value.
11. Information regarding the tilt series is saved in the database to make movie upload possible.
