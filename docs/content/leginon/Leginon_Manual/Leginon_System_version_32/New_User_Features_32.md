## JEOL JEM 1400 and above control (using JEOL TEMCOM)

See [JEOL installation specifics](/leginon/JEOL_installation_specifics) and [Operation Notes](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_microscope_computer_30/JEOLCOM_installation_specifics/Leginon_Operation_for_JEM_scopes)

### What does not work

-   Usage of Piezo Stage for fine stage movement does not work.
-   Omega filter alignment does not work. We can only insert/retract the slit for now.
-   Moterized aperture control alignment is not implemented.

### User Features specific to JEOL TEMCOM scopes

1.  MSI-T Application designed for JEOL socpes with large LOW MAG hysteresis #3669.
2.  Automatically open column valve before taking an image #3267

## General

1. Automatically lift screens before an image is taken #3002.

2. Enhanced TargetPanel.py to read specific frame of an image stack #3561

3. Allow users to specify preset name during image upload #3382

4. RCT feature matching with opencv #3020 (Contributed by Peter Kraft)

5. Option to pause longer on the first target imaged from a list #2959

# Calibration Tools

1. Manual image beam shift compensation calibrator for JEOL scopes #3291

2. Script for copying K2 counting mode calibration to super-resolution mode #3247

# Administrator Tools

1. Restrict projects seen by the users during Leginon Setup #3184

2. Handling of MRC frame interception of Falcon II movies #3238

3. Allow mysql port to be specified in sinedon.cfg #3028

4. Allow sinedon.cfg, leginon.cfg and redux.cfg locations specified with environment variable #18698

5. Tools for archiving Leginon project data #2915

# Developer Features 3.2

1. Camera Simulator subclass that mimics K2 camera counting and super-resolution mode #3359

2. Append and write labels to mrc files #2983
