## Taking final exposures on film

If film is used to collect data with one or more exposure presets, Edit the preset setting in Presets Manager when you are ready to do so. The exposure time of the preset will be applied to film exposure. A warning message will come up when the cassette is exhausted and Leginon paused. You will need to reset the stock number after new film is added.

## Acquiring images with the stage at a fixed alpha tilt

All targeting and focusing works on tilted specimen with correction made within Leginon automatically.

1. Z adjustment to the defocus allows images acquired from image-shifted targets to exhibit equivalent defocus regardless of location.

Additional [stage position matrix calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Stage_Position_matrix_calibration) is therefore needed for MSI at hl preset magnification where the targets are selected in Hole node.

2. Distortion correction is made to beam-tilted images that are used for autofocusing to boost peak signal.

Rotation centers are therefore needed to be stored at the magnification and HT for fa and hl that are used in Z focus and Focus nodes for autofocusing, respectively. This is [stored (and retrieved) in Beam Tilt node of Calibration application](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Autofocus_Calibration_with_Beam_Tilt_Node#Rotation-Center-Storage-and-Retrieval). Because rotation center may change from day to day, the correction is made only if the required rotation center is stored under the same session.

**Because of the additional calibrations, this is not recommended for beginners.

[< MSI set-up in more details](/leginon/MSI_set-up_in_more_details) | [MSI Operation >](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_Operation)
