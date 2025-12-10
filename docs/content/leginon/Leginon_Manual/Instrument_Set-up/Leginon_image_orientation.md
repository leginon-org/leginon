Leginon uses mrc format to save images. Since we were not aware of a standard mrc format display orientation, we have chosen at the time of the early development a display orientation in all Leginon related product in which the origin of image data is located at the top left. The first row of the displayed image comes from the first few data bytes so that horizontal axis is the fast axis. This is the standard for scanning display and allows fastest display because it is consistent with the hardware.

We thus require users and installers to flip/rotate their image orientation set by camera configuration so that the orientation of the image shown in Leginon display is the same as what appears to the user looking down the main screen when they face the microscope.

Fail to follow this orientation might cause unexpected behavior. For example, if you use stage tilt to adjust z height to eucentric, an image of a flipped image will trick Leginon into adjusting the z stage position in the opposite direction. If you use Appion to process images involving tilts, such as tomography and RCT, the structure would come out to be in the wrong hand.

[< Calibrations required on the microscope alone before starting Leginon](/leginon/Leginon_Manual/Instrument_Set-up/Calibrations_required_on_the_microscope_alone_before_starting_Leginon)
[Gatan camera setup >](/leginon/Leginon_Manual/Instrument_Set-up/Low_dose_shutter_configuration_for_Gatan_camera_in_Digital_Micrograph_program)
[Tietz camera setup >](/leginon/Leginon_Manual/Instrument_Set-up/Tietz_camera_configuration)
