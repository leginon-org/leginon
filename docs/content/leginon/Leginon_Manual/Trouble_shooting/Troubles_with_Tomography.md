## Unusual intensity range in the tomography image

Two possible reasons:

1.  The exposure time has been modified by the tomography node to spread the total dose to all images in the tomogram.
     
    Solution: Reduce the total dose or reduce preset beam intensity. You can find the real exposure time from the log panel of the tomography node or through the information page of the image in the web image viewers.
     
2.  The image intensity of images collected by the Tomography class node does not have the same meaning as in other images in Leginoon. The flat-field corrected intensity values are multiplied by 10 before the image is saved and displayed as MRC image as signed 16-bit integer. Therefore any original CCD count of 3276.8 or larger will overflow. All other images in Leginon are saved without manipulation as float. Therefore, the images obtained through tomography node and another acquisition nodes will appear differently in the both the web image viewer and within Leginon.
     
    Solution: Reduce the total dose.
     
    Find out what exposure time corresponds to the fractionated dose from your tilt angle step and range and total dose and take an image at tomo preset with such an exposure in Navigation node. You will need to reduce the total dose if a good fraction of the counts are larger than 3200 even though it would not appear to be saturated in the float scale without the 10x factor.

## Large movement between tilted images

Find out how smooth the movement is by comparing the images.

If transition is smooth and linear:

1.  Magnification too high
     
    Solution: Lower the magnification or perform [low-magnification rough model fitting](/leginon/Leginon_Manual/Leginon_MSI-Tomography_Application/Running_the_application).
     
2.  Optical axis offset model is too different from the initial guess for the non-linear least-square fitting.
     
    Solution: Perform [low-magnification rough model fitting](/leginon/Leginon_Manual/Leginon_MSI-Tomography_Application/Running_the_application).

If transition is not smooth nor linear:

1.  Goniometer behavior unpredictable
     
    Solution: Service the goniometer.

## Failure of xy feature tracking

Feature tracking in x and y axes is a 2nd order polynomial fit of preceeding data points. The default uses 5 data points. When a sudden jump occurs in the tracking error, it
tend to follow the trend of the last point. If the jump is a temporary clich in the goniometer, this tend to over correct the tracking error and eventually loose track as shown
in Figure 1. A possible fix is to increase the number of data points in the fitting. This can be set in the tomography setting "Smooth n tilts for defocus prediction". 4 in defocus
prediction is equivalent to 5 points (n+1) for xy tracking.

**Figure 1**
![](images/tomoxbad.png)

## Large tracking error between the first and second tilt images

The first image in each tilt group of the tilt series at the "start" angle (normally 0 deg) and the second image at tilt of "step" angle from the "start" angle do not use the
fitted model. It is assumed that the eucentric height judged by stage alpha wobbling in the "Tomo Focus" node gives a stage height that the tracking of feature by such a small tilt
would be good enough. In most cases this is a reasonable assumption. However, we have had experience of goniometer alignment problem where the assumption fails. The symptom is
illustrated in Figure 6 below. Note that the Feature tracking error is displayed as percentage of the image length.

**Figure 2**
![](images/tomoz0bad.png)

This tilt series was taken with a starting angle of zero and at an image size of < 1 um. As can be seen here, apart from the 2 and minus 2 degree tilts, the tracking error was less
than 2 % of the image. Only the tracking of the feature between 0 and +/- 2 degrees are large. At close to 20 % error, this made the overlap between plus and minus 2 degrees unacceptable and
often cause popular alignment programs to misalign the two half of the series.

The first solution is of course to report it to your microscope service engineer. When we had this problem, many users noticed that it was difficult to adjust stage to eucentric height manually with alpha wobbler. Features jumped while the goniometer changed rotation direction. In addition, different magnitude of tilt range suggests different eucentric heights. It is not easy to fix this, so it might take a while. At the end, a loose screw was found which makes the motor slips when it starts to tilt in one of the direction.

Before the hardware is fixed physically, it is still possible collect tomograms. The model fitting of the overall curve in the above case gave z0 of +5 um through the whole tilt series (Figure not shown). Therefore, by moving the stage up by such an amount after the stage-tilt-based autofocusing can bring us to the correct height for tomography. This can be acheived by saving the "tomo eucentric" focus current to the database, align rotation center for this stage height and focus. Then change the correction type of the "Beam_Tilt_Fine" focusing step to "Stage Z".

## Failure of model-based correction

The model used in the defocus correction in Leginon tomography node is a very simplified one. There are a few cases when the approach fails. Here are ones that we have encountered:

## Y-axis looping

The microscope goniometer does not move on only the tilt axis. With its complex structure, a common problem is that when the stage is highly tilt, the position slips in the y-direction. This is known as looping. Figure 3 shows an example of this problem.

**Figure 3**
![](images/tomoxyloop.png)

While the x-axis position shifts monotonically as a stable model should be, the y-axis in the positive tilt direction changes little from 0-30 degrees before it increases rapidly after 30 degrees. Even though the tracking in xy plane is still good, the defocii correction at these higher tilts may no longer be correct if the tilt axis parameters are fitted dynamically. Figure 4 shows the model parameters of the same tilt series where the fitted phi and offset starts to change above 30 degrees even though the tilt axis has not moved according to the shrinking behavior of the images during the tilts. Note that in this particular case the looping problem is still mild so that the over-correction is not very strong. only a small slope change is resulted in z0 prediction. In worst cases, the defocus over-correction is so large that the adjacent images can not correlate properly and even the xy tracking would fail. The spikes around zero tilt is a display data sorting error of the identical starting tilt of the two tilt groups.

**Figure 4**
![](images/tomomodelloop.png)

Other than asking microscope service engineer to fix the looping, one can find the best fixed model in the series to apply to future tilt data collection. To make the fixed
model permantly saved to the database, follow these steps:

1.  tomography/settings/model>activate "keep the tilt axis parameters fixed".
2.  tomography/settings/model>initialize the model with "custom values". Enter best estimate of the fixed model. For example, in the positive direction, enter phi as
    --2.17 degrees and axis offset as --1.52 um. since these are the stable values up to the point the y-looping starts.
3.  tomography>collect a full tilt series. If the run is successful with good tracking in all three axis, the model will be saved in the database for this
    magnification.
4.  tomography/settings/model>From now on, you can initialize the model with "only this preset" or "this preset and lower mags"

## Grid slips between the first and second tilt directions

When the holder does not hold the grid tightly, the grid slips to a different position when the first tilt direction ends and the goniometer quickly returns to zero tilt. Leginon is designed to adjust the target before the second tilt group starts. The default setting for this function is to use only the parent image (i.e. one ancestor) where the target comes from as reference. If the slip is larger than the size of the parent image, the adjustment may fail, and a random target would be acquired in the second tilt group.

Starting from Leginon 1.6, the target adjustment can be done with all ancestor images of the target by choosing "all" in the acquisition part of the tomography node setting to adjust target with all ancestors. The node "Target Adjustment" limits the lowest magnification that this target adjustment would go up in ancestry. The default is at 300x so that the presence of the objective aperture does not create difference in the reacquired ancestor image from its original.

## Strong and continuous specimen drift

The model used in Leginon considers any shift of feature in the image a result of tilt axis not aligning to the center of the detector. With the phi and offset fixed, all errors are accumulated in z0 and results in bad defocus correction. There is no solution to this at the moment.

[< Troubles with Calibrations - Troubleshooting](/leginon/Leginon_Manual/Trouble_shooting/Troubles_with_Calibrations_-_Troubleshooting)
