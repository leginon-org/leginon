## Adjust settings in Leginon

**IMPORTANT**
The protector for Falcon camera increases the wait time the electron beam becomes available for image acquisition. You must set Leginon settings for the following operations:

1. In any MSI application, open the settings for "Target Adjustment" and set "Wait for x seconds before reacquiring image" to 2.5 second minimal.
2. In all MSI applications, node that does autofocus with beam tilt, open the settings and set "Beam Tilt Settle Time:" to 0.75 second minimal.
3. In any MSI application, open the settings for "Presets Manager" and give enough pause time between preset changes. This may need to be done experimentally depending on cycling settings. If the pause time is not sufficient, images in "Align Presets" tool will appear blank from time to time.

Falcon images also produces very sharp phase correlation peak on Titan Krios. If it is causing a failure of peak search during various calibration, change the low-pass filter settings where it occurs.

## Preparation in TUI/TIA

### Acquire Gain/Dark References

Follow [Falcon gain correction](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Falcon_camera_support/Falcon_gain_correction) section

## Recommended dose rate

The optimal dose rate is likely between 3 - 3.5 electrons/pixel/frame or 50-60 electron/pixel/s based on available literature of high resolution structures using this camera.
If you have to use lower dose rate, check the validity of the gain reference.

## Preset Recommendation

An example can be found in [Pre-MSI Set-up#Preset-Design-Example-for-Falcon-II-on-Krios](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Pre-MSI_Set-up#Preset-Design-Example-for-Falcon-II-on-Krios)
