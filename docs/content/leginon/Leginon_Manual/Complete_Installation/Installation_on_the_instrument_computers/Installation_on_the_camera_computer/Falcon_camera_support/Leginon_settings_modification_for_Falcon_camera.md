**IMPORTANT**
The protector for Falcon camera increases the wait time the electron beam becomes available for image acquisition. You must set Leginon settings for the following operations:

1.  In any MSI application, open the settings for "Target Adjustment" and set "Wait for x seconds before reacquiring image" to 2.5 second minimal.
2.  In all MSI applications, look for nodes that do autofocus with beam tilt (For example "Z Focus", "Focus", "Tomo Focus" etc.), open the settings and set "Beam Tilt Settle Time:" to 0.75 second minimal.
3.  In any MSI application, open the settings for "Presets Manager" and give enough pause time between preset changes. This may need to be done experimentally depending on cycling settings. If the pause time is not sufficient, images in "Align Presets" tool will appear blank from time to time.

Falcon images also produces very sharp phase correlation peak on Titan Krios. If it is causing a failure of peak search during various calibrations, change the low-pass filter settings where it occurs.
