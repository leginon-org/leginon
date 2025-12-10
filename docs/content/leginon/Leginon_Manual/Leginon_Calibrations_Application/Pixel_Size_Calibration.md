Pixel Size Calibration allows entry and simple extrapolation of pixel size values for various magnifications. The entry value should be calculated in (m/pixel). Enter pixel size for all the magnifications that will be used. Extrapolation can be used to enter the pixel sizes for magnifications that have not been calibrated at the microscope with a standard specimen, such as catalase crystals.

**JEOL scope needs good pixel size calibration at presets used for lower magnification presets such as hl and sq to refine scale values in jeol.cfg**. Please use diffraction grating replica to do this at the defocus that will be used in the experiment as described at the end of this page.

## Confirm the camera settings by taking a test image with a preset sent to scope

## Enter a known pixel size

1.  Leginon/Pixel Size/Toolbar> Click the Calibrate button ![](images/play.png).
     
2.  Leginon/Pixel Size/Pixel Size Calibration> Highlight the desired magnification and click Edit.
     
3.  Leginon/Pixel Size/Pixel Size Calibration/Edit Pixel Size> Enter the pixel size in m/pixel.
     
4.  Leginon/Pixel Size/Pixel Size Calibration/Edit Pixel Size> Enter a comment to describe how this pixel size was determined.
     
5.  Leginon/Pixel Size/Pixel Size Calibration/Edit Pixel Size> Click Save
     
6.  Leginon/Pixel Size/Pixel Size Calibration> Click Done

## Extrapolate a pixel size

1.  Leginon/Pixel Size/Toolbar> Click the Calibrate button ![](images/play.png).
     
2.  Leginon/Pixel Size/Pixel Size Calibration> Highlight 1 or more magnifications to extrapolate the new mag. pixel size from.
     
3.  Leginon/Pixel Size/Pixel Size Calibration> Click Extrapolate
     
4.  Leginon/Pixel Size/Pixel Size Calibration/Extrapolate Pixel Size> Highlight the desired magnification to extrapolate the pixel size for.
     
5.  Leginon/Pixel Size/Pixel Size Calibration/Extrapolate Pixel Size> Enter a comment to describe how the new size was determined.
     
6.  Leginon/Pixel Size/Pixel Size Calibration/Extrapolate Pixel Size> Click Extrapolate and Save
     
7.  Leginon/Pixel Size/Pixel Size Calibration> Click Done
     
    **Pixel Calibration Need for the Example MSI:**
     
    |*.Preset|*.magnification|
    |gr|120|
    |sq|550|
    |hl|5000|
    |fc,fa,en,ef|50000|

## Acquire images of a standard crystal and calculate the pixel size from distance between the diffraction spots

1.  TEM>Insert the standard crystal such as catalase, aligned to eucentric height, and centerred on a well ordered area at 0.5-2 um. defocus.
     
2.  Leginon/Pixel Size/Toolbar> Click the Acquire button ![](images/acquire.png). The power spectrum of the image will be displayed.
     
3.  Leginon/Pixel Size/Toolbar> Click on the Measure button ![](images/ruler.png) if several orders of diffractions can be seen.
     
4.  Leginon/Pixel Size/Pixel Size Measurement> Enter the lattice parameters of the crystal. The default is that of catalase.
     
5.  Leginon/Pixel Size/Panel> Use the ruler tool to measure the distance of two well-separated diffraction spots.
     
6.  Leginon/Pixel Size/Pixel Size Measurement> Enter the Miller indices of the spots and the distance measured in pixels on the spectrum.
     
7.  Leginon/Pixel Size/Pixel Size Measurement> Click on "Calculate Pixel Size". The result is shown below.
     
8.  repeat 5-7 on other pairs of spots or repeat the measurement. Alternatively, go to another crystal and repeat 2. (There is no need to close the settings window. The values calculate will stay until the TEM magnification of the image has changed.
     
9.  Leginon/Pixel Size/Pixel Size Measurement> Select from the pixel size calculated so far by highlighting them for averaging and save to database with a click on "Save Averaged Pixel Size From Selected".
     
10. Leginon/Pixel Size/Pixel Size Measurement> Click Done

## Measure pixel size at lower magnifications using Diffraction Grating Replica.

If the diffraction grating replica is calibrated to be N lines per mm, and M line spacing gives a pixel distance of D binned pixels with B times binning of the camera, then the pixel size in meters is

    M / (1000*N*D*B)

You can measure D from images taken using the ruler tool ![](images/ruler.png) in image panel whichever node you have taken the image of the diffraction grating replica.

[< Calibration without presets](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Calibration_without_presets) | [Bright and Dark reference images >](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Bright_and_Dark_reference_images)
