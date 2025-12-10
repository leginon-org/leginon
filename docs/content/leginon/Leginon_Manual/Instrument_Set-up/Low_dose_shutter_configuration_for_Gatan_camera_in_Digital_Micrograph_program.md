Leginon uses Digital Micrograph software came with any Gatan camera to aquire images through a function call. It is therefore necessary to configure the camera in Digital Micrograph and the configuration need to be checked and be consistent among users of Leginon in order to use the same calibration.

First, find out which camera control digital output is connected physically to the pre-specimen shutter on the microscope. This should be the shutter used for low-dose imaging (beam-blank or pre-specimen shutter). You will need to find it out from your microscope engineer or those who install the camera. In most cases we've seen, this is shutter 1, also known as primary shutter in DM. The next part uses this as the example.

Second, start DM from the Menu bar, go to /Camera/Configure Camera...

This brings up the Camera Configuration Window.

1.  Set Shutter 1 to what is connected physically to your camera control box. In this examples, pre-specimen shutter. Set Shutter 2 to the other one (post-specimen in this example).
2.  Choose the Idle Shutter State. For low-dose mode, only pre-specimen shutter is used. Therefore, in this example, you would set Shutter 1 to closed and leave Shutter 2 to open.
3.  Choose to flip the camera axis if desired. Our standard at NRAMM makes the image acquired and displayed in DM or Leginon to have the same orientation as what is viewed as one sit at the microscope. You can check it by acquiring an object of known orientation such as an offsetted pointer device. At NRAMM, this happens to require a flip.

Third. now that the exposure will need to be made by opening the pre-specimen shutter, We do not know exactly which if any of the three built-in recording mode is used by the function call from Leginon, but they should be consistent in low dose imaging, any way. This is under the menu /Camera/Camera Setup

For each of the mode (Search/Focus/Exposure), since in this example shutter 1 (primary) is the pre-specimen shutter that is normally closed, you should uncheck the box on "Use Alternate Shutter".

To check that your shuttering is right, you need to look at the LED on the camera control box. While the microscope main screen is down, LED lights for the two shutters should be on, meaning the shutters are open. When the main screen is up and the camera is inserted, the shutters would go to idle state, with the one corresponds to the pre-specimen dimmed while the one for the post-specimen lit. Next, try to acquire an image through Leginon at a relative long exposure ( > 0.5 s), and watch the LEDs. The one for pre-specimen should light up during the time of the exposure and then become dim again.

Camera flipping and shutter settings are configured per computer user. If you have several users, you will need to sync the flipping practices and make sure all of you are shuttering correctly.

Also as a warning, different data acquisition packages also require different configuration. If you have users using SerialEM, for example, it is important to coordinate with them to avoid conflicts.

### For Complete Installation, go to [Calibration Application](/leginon/Leginon_Manual/Leginon_Calibrations_Application) Chapter next.

[< Leginon Image Orientation](/leginon/Leginon_Manual/Instrument_Set-up/Leginon_image_orientation) | [Good Alignments Save Time>](/leginon/Leginon_Manual/Instrument_Set-up/Good_Alignments_Save_Time)
