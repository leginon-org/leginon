Follow FEI's instruction in obtaining Gain/Dark References.

-   Take an single exposure first in its Reference Manager Tab to make sure the intensity range is adequate.

If you plan to save frames, make sure you repeat the process with "Store intermediate images" option on in C:\Titan\Exe\IntermediateImageTool.exe.

-   Take an exposure in your final exposure condition, including the [frame bin configuration](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Falcon_camera_support/Falcon_gain_correction/Falcon_raw_frame_saving_configuration_xml) with "Store intermediate images" option on to check if the correction is properly applied.
-   If that does not work, try configuring the frame bins with single base frame instead (worked for us) in this process.
