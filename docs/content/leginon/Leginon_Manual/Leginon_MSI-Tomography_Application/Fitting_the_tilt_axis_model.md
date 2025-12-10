## Find the Rough Tilt-Axis Location Manually

The easiest way to find the tilt axis uses the fact that the projected feature moves according to a cosine function when it is off from CCD or optical axis but not off from eucentric height.

Do this at the microscope:

1.  Use stage alpha wobbler (symmetrical tilts) to put the specimen to eucentric height.
2.  Send to scope alternatively between 0 and 30 degree. Track the position of an object near the center of the viewing screen at the magnification you want use the model. If the tilt axis does not pass the center of the screen, the object will move upon this asymmetric movement.
3.  Move image shift x,y until the asymmetric tilt movement is minimized.
4.  Use a larger tilt to do the same if desired.
5.  Check the asymmetric movement between 0 and --30 degree to make sure it works reasonably in both way.
6.  Save the image shift as tomo preset's image shift.
7.  Estimate the combined image shift sqrt(x^2+y^2) and enter that as the custom, tilt axis-offset.
8.  From what is observed during the tilts, estimate the direction of the tilt axis and entered as the custom phi value.
9.  Perform the quick test run with this custom *Fixed Tilt Axis Model"

## Shift the tomo preset to the tilt axis

Tilt models used in Leginon is not complete and will more likely to deviate the real behavior when you are away from the axis. To minimize this, it is best to set the tomo preset image shift to the axis. The manual procedure above gave how to find this value. It can also be obtained by clicking the "reset learning" button.

## Quick fixed model test run

Instead of a full range tilt series, much can be learned at low tilts. Again, this uses the fact that defocus changes in a sine curve when the tilt axis is off.

Use Leginon Tomography to do a small range tilt since sine curve has the highest slope around zero.

1.  Set the tilt series to cover max 8, min 8 and step at 2 deg.
2.  Take tilt series at these low tilts and at an area where defocus change can be observed easily. Increase dose if needed.
3.  Compare the defocus of the resulting images. Optimize the tilt axis offset so that defocus differences among the tilts in the same tilt direction is minimized.

## Full Length Tilt-Axis Model Testing and Fitting

Test runs should be done at the magnification, defocus, and tilts up to the highest values planned for the real ones with a specimen with isotropic features in view and
adjusted to eucentric height. Tilt steps should be made to allow at least 15 images taken per tilt direction. Note that this can refine the above rough results but may give
worse results at times.

### First Test Run: Fixed Model

The first time the tomography application is used on a microscope, all model
parameters are default to zero. A test run should be done with the specimen at eucentric
height and all default settings including "keep the tilt axis parameters fixed" activated.
If the feature tracking is good, and the defocii of the images in the tilt series do not
significantly changed, the goniometer behavior and camera alignment are close to ideal,
and no improvement of the model is required.

If the xy tracking deteriorates quickly in the first few tilts, the magnification
should be dropped so that tracking is possible through out the tilt series. Once a rough
model is established, refinement can then be done at higher magnifications.

### Runs to Improve the Model-Fitting

A complete tilt model fitting is difficult with small number of data points or at only
low tilts. Therefore, two tilt series need to be taken in order to get a good averaged
model that is later fixed.

1.  tomography/settings/model>deactivate "keep the tilt axis parameters
    fixed".
2.  tomography/settings/model>initialize the model with "this preset only" unless
    this is a refinement of a rough model obtained at
    a lower magnification, in which case, initialize the model with "this preset
    and lower mags".
3.  tomography/toolbar>click on "reset learning" ![](images/refresh.png) to have
    a fresh start of tilt series data included in the fitting.
4.  Presets Manager>send the "tomo" preset to scope.
5.  tomography>Start the tilt series image collection by clicking on "Simulated
    Target" tool.
6.  repeat 4 and 5 to dynamically fit the model the second time if the first one goes
    to completion.
    If the target shifts away during the run, reduce the magnification, repeat 1
    through 9 in this procedure and then return to the higher, intended mag and refined
    the model using the same procedure and proper setting for refinement as mentioned in
    2.
7.  Check on web image viewer to see if the result of the second run in step 6
    produces images of constant defocus through out each half of the tilt seriese.
8.  If the model is good, activate "keep the tilt axis parameters fixed" in the
    tomography settings.
9.  Repeat step 2. Other than reset the learning, the tool produces an output of image
    shift you should copy down and apply to the "tomo" preset in the future runs.

## Understand the results of the model fitting

If the above procedure does not yield a good model, it is necessary to study the graphs
output by the run to determine possible causes and derive the best fixed model that at least
work for most angles.

See [Fitting the tilt axis model](/leginon/Leginon_Manual/Leginon_MSI-Tomography_Application/Fitting_the_tilt_axis_model) for definition of the displayed values

### First fitting tilt series

Figure 1 shows a typical result from the first dynamically fitted tilt series run. x and

**Figure 1**
![](images/tomoxyz1.png)

According to the Zheng et. al. model, the tilt-axis can be characterized by three
parameters: phi, the angle between the tilt axis and the detector x axis (column), offset,
the distance between the center of the detector and the tilt axis on the xy plane, and z0,
the distance between the specimen from the xy plane that contains the tilt axis.

As a first tilt series used in the model fitting, the data is not fitted until it
accumulate enough data points and spread over more tilts. We arbitrarily select 30 degrees as
the starting angle where the fit is started.

As can be seen in Figure 1, the model is significantly different from the initial as z-axis "Prediction" jumps once the fitting is started. In particular, the model z0 which corresponds to the offset of the specimen from the tilt axis in z direction dominates deviation. Such problem is evident by the near-straight line feature shift in x-axis over more than 1 um. There is also some offset in
x direction since the "Prediction" and "Position" flattens somewhat as it approaches zero tilt. The tilt axis has minimal tilt from x-axis since in the y-direction, despite the bump at about 40 degrees, the range of variation in the whole tilt series is about 0.06 um.

By activate "show model parameters" check box in the viewer, more plots are shown
(Figure 2). phi and "optical axis" offset remain fixed below 30 deg while z0 is recalculated at each tilt. As you can see, the fitting of the former two parameters are not very stable in this first trial. Therefore, we need to do the second run.

**Figure 2**
![](images/tomomodel1.png)

### Second fitting tilt series

Figure 3 shows the z-axis plot of the second run since the x and y does not change
significantly. Figure 4 shows its corresponding model parameters. The zero and first tilt
uses the initial model and the rest are fitted dynamically. In this run, because more than
one tilt series is found in the memory since last "reset learning", the model fitting starts
after the first tilt image is acquired. model parameters are rather stable over the whole
tilt series and suggests that the tilt axis is tilted from x-axis by about --1.3 degree, and
offset from the center of the detector by --0.6 um, and the specimen is off from eucentric
height by about --0.7 um

**Figure 3**
![](images/tomoz2.png)

**Figure 4**
![](images/tomomodel2.png)

Although it is not possible to maintain perfect defocus prediction in the full range of
the tilt by using a fixed model, we found that the overall performance is better if an
average tilt axis model that works well in the mid-range tilt is used as a fixed model. For
example, for the behavior in the above figure, we choose:

### Fixed axis tilt series

Use these custom values as initial model and turn on "Keep the tilt axis parameters
fixed". If the result is good, judging by consistent defocus and target tracking through out
the tilt series, this model will be saved in the database as best model automatically, and
you can revert back to initialize with the model of "only this preset".

## Low Magnification Model Fitting

The fitting of optical axis offset does not always works if the offset is so large that
the feature moves out of view with even a small tilt. In such a case, it is worth first
collect a tomography series at a lower magnification to define roughly the model.

At beginning of each session, or forced by the user, the model is initialized. By
default, at the initialization, Tomography node uses past fitting results that show good
agreement with the experimental data at the magnification of the preset used. If a good
model is not found, that from lower magnifications will be used. It is possible to force the
node to use a model fitted at a particular magnification by selecting it in
Tomography/Settings/Model.

Therefore, we recommend that, in case of fitting failure on good contrast images, the
followings should be done:

1.  Tomography/Settings/Image Acquisition> change the preset to "hl".
2.  Tomography/Settings> adjust Tilt and Exposure parameters to match.
3.  Acquire the tiltseries images.
4.  If the tracking is good, change the preset back.
5.  Tomography/Settings/Model> Initialize with the model of (the mag of "hl"
    preset).
6.  Acquire the tomo-series.
7.  If tracking is good, change back to Initialize with the model of "this preset and
    lower" mag.

See [Troubles with Tomography](/leginon/Leginon_Manual/Trouble_shooting/Troubles_with_Tomography) section for various modeling problem solving examples

[< Reading the tomography graphs](/leginon/Leginon_Manual/Leginon_MSI-Tomography_Application/Reading_the_tomography_graphs) | [Full Protocol on a F30 with an energy filter >](/leginon/Leginon_Manual/Leginon_MSI-Tomography_Application/Full_Protocol_on_a_F30_with_an_energy_filter)
