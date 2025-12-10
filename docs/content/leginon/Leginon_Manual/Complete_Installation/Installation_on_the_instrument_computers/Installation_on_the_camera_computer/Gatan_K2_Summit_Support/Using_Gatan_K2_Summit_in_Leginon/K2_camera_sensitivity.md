K2 Summit has different camera sensitivity value in different modes.
Enter the values in [Dose\ (Camera Sensitivity)\ Calibration#Enter-pre-determined-camera-sensitivity-value](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Dose_Camera_Sensitivity_Calibration#Enter-pre-determined-camera-sensitivity-value)

## Linear mode:

This behaves like classical CCD/CMOS sensor. One pirmary electron event generate current that is counted by A/D convertor. The camera certificate provided by Gatan should contain this value under "Detector Conversion Efficiency (sensitivity). The value depends on the energy of the electron.

## Counted mode

In this mode each primary electron event is fitted and registered as one count. Therefore, the sensitivity is roughly 1. With higher dose rate, coincidence loss will reduce the number. If you are always using the camera at a fixed dose rate such as 8 e/pixel/s, the best way to get this value is from DM interface and compare that with the mean value you get in Leginon under the same imaging condition.

1.  Check DM Search mode configuration: Make sure you are using counted mode, exposure time of 1 second, and binning is 1.
2.  Srart Search mode imaging, adjust the beam intensity until the displayed dose rate value in e/pixel is what you want, let's say it is 8 e/pixel/s.
3.  Stop Search mode. Take an image in Leginon using Navigation node for the same length of exposure with the same beam intensity. Look at the mean value of the image.

Leginon counts per primary electron = Leginon mean counts / 8

-   The reason that we take an image in Leginon is that DM adds a scale factor to its image to account for coincidence loss after its software gain correction. Leginon, taking the uncorrected raw count and does its own gain correction, does not apply this scaling.

Typical value is around 0.9.

## Super-resolution mode

Super-resolution mode is a positional division of counted mode. The sensitivity value is exactly 1/4 of that of the counted mode.
