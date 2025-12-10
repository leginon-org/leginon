-   Recommended for all FEI scopes

## Purpose

Leginon and its subsystem pyscope uses the property Illumination.RotationCenter in Tecnai/TEM Scripting to set/get beam tilt values. We have noticed that some version of the TEM or Tecnai Scripting defines the function for set/get Ilumination.RotationCenter in units other than the original radians. Known versions with this problem are Tecnai 3.1.1 are Titan 1.0.0. We also know that it is fixed in Tecnai 3.1.2 and Titan 1.0.2 (Thanks to Wim Hagen for the information). Since Leginon need the values in radians, a scale factor need to be assigned. We do not not know which version requires non-default scale factors. Therefore, we recommend that all scopes be checked before using Leginon MSI applications with beam-tilt-based autofocusing.

-   The most likely values are 1.0 and ~6 and it does not need to be very accurate. Please let Leginon team knows if yours is very different from these.

> **Note:** See [running get_beamtiltscale.py](/leginon/Leginon_Manual/Instrument_Set-up/Calibrations_required_on_FEI_microscopes/TEM_Scripting_Beam_Tilt_Calibration/Running_get_beamtiltscalepy)

## Making the change in tecnai.py

1.  In the same folder, find **tecnai.py** Open it with a plain-text editor or python's IDLE and look for the following lines close to the beginning of the file.
        # This scale convert beam tilt readout in radian to 
        # Tecnai or TEM Scripting Illumination.RotationCenter value
        # Depending on the version,  this may be 1.0 or closer to 6
        rotation_center_scale = 1.0
2.  replace the number in the last line with the rotation_center_scale determined while running **get_beamtilt_scale.py**
