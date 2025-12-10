The main use of K2 Summit is in Counted or Super-resolution mode in combination with dose fractionation (frame saving).

If you want to use DM's dose fractionation, activate the "save frames" check box in the particular preset camera configuration. DM's frame alignment algorithm is no longer supported in the gui in 3.1 since it affects throughput greatly and is not the best there is.

* [K2 Summit introduction](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Gatan_K2_Summit_Support/K2_Summit_introduction)
* [Acquiring summed frame image thru Leginon](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Gatan_K2_Summit_Support/Using_Gatan_K2_Summit_in_Leginon/K2_acquire_image)
* [Gain and Dark Correction](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Gatan_K2_Summit_Support/Using_Gatan_K2_Summit_in_Leginon/K2_gain_correction) **This involves both DM and Leginon**
* [Pixel and Matrix Calibrations](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Gatan_K2_Summit_Support/K2_calibration)
* [Camera Sensitivity Measurement](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Gatan_K2_Summit_Support/Using_Gatan_K2_Summit_in_Leginon/K2_camera_sensitivity)
* [Trigger raw frame saving](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Gatan_K2_Summit_Support/Using_Gatan_K2_Summit_in_Leginon/K2_raw_frame_saving)
* [Transferring raw frame images](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Direct_Electron_DE-12_direct_detection_device_support/DDD_raw_frame_file_transfer) off the hard drive of K2 Summit during data collection to a network drive.
* [Compiling corrected movie stack](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Gatan_K2_Summit_Support/Make_DDD_movie_stack) with Appion using bright and dark images acquired in Leginon

## Warning

-   Because of a delay in communication with DM when Leginon is started, camera configuration shown in Correction Node settings may not corresponds to what is used last time when you quit Leginon. Make sure you check this.

## Leginon functions that do not work with K2 camera

### General functions

1.  The dose matching tool in Preset Manager. K2's exposure time is not fine grained enough to make small adjustment according to the small dose deviation. You will have to use fixed exposure time and adjust beam intensity by hand to achieve the right dose. We find out the equivalent screen reading from the microscope for the acceptable 8-10 e/physical pixel/s dose rate for the detector and make adjustment there.

### Frame saving camera functions

1.  The image returned to Leginon display is always integrated over all the frames with K2 summit camera. Selection of frames to use as in DE series does not work here.
2.  Readout delay is not adjustable on K2. Leave it at 0.

## Clean up

Frame saving generates a lot of files during acquisition and during processing.

1.  python script in leginon directory "cleanddraw.py" can help you clean up the transferred raw frames when you start to run out of disk space. See Feature #1784 for more details.
2.  Selective removal of aligned frame stack in Appion runs is still to be written.

[^ Instrument Usage Specifics](/leginon/Leginon_Manual/Instrument_Usage_Specifics)
