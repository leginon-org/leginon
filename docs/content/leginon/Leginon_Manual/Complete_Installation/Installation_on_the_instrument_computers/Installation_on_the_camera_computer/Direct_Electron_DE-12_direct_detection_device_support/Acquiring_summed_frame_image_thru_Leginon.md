## Camera Configuration

Refer to [introduction](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Direct_Electron_DE-12_direct_detection_device_support/DE-12_introduction#Camera_Settings_for_DE-12) on the options

1.  Select DE12 as the camera
2.  Uncheck "save raw frames"
3.  Leave "Frames to use" empty to sum up all frames

## acquire [Bright and Dark reference images](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Bright_and_Dark_reference_images)

Leginon does not research references by frame rate and sensor temperature. If you change either of them, you will need to acquire new references.

Use valid exposure time (multiple of frame time length)

**Use long positive readout delay time (>= 2 frame length) to ensure uniform intensity readout on the first recorded frame.**

It does not matter whether you save raw frames or not in this process. Leginon does not use them for corrections.

### typical number of dose rate, number of frames, number of images used in reference image acquisition at NRAMM

We have been using the following numbers. However, we did not do a systematic study on what is required, so it might not be optimal:

-   dose rate: 4 electron per pixel per frame (similar to our typical dose rate for experiment)
-   number of frames in summed image: 10 (i.e. 407 ms if using the default 24.57 frames/second)
-   number of images for averaging: 20

## Usage

1.  Select DE12 as the camera, configure and uncheck "save raw frames" in the camera configuration of the preset that you want to use and go for it.
