Corrector handles image corrections before it is displayed and saved. It has three functions:

-   Acquire dark reference image


-   Create the normalization images (called gain reference in Gatan Digital Micrograph) by acquiring bright images and through some calculation.


-   Upon the request by another node, load the dark and normalization image from the requested channel and perform the dark subtraction and flat-field correction.


-   Perform addition corrections such as despiking, intensity clipping, and specific pixel/column/row intensity correction to the flat-field corrected image above.

Required bindings: None

## Dark Subtraction

When an image is taken without electron beam, the image readout is not always zero. This level of the offset always present in the raw image with or without
the beam. Therefore, it needs to be subtracted from any raw image before flat-field correction.

There are two component in the dark readout, bias and dark current. Bias is not exposure time dependent while dark current is.

Therefore, the pixel value used for dark subtraction should be

    Dark_Pixel_Value = Bias_Pixel_Value + Dark-Current_Pixel_Value * exposure_time_scale_factor


where exposure_time_scale_factor is the ratio of the exposure time between the image to be corrected and the dark image acquired.

Currently, Leginon corrector does not yet have separate record of the bias and dark current, so different strategy is required. We plan to improve it. Here is what we do currently:

### Counting mode in K2 Summit:

No Dark Subtraction is needed.

### Frame-saving camera (K2 linear/base and DE):

These have CMOS sensor and their dark readout is dominated by dark current. Therefore, in this case

    Dark_Pixel_Value = Dark-Current_Pixel_Value * exposure_time_scale_factor

-   In K2 counted/super-resolution mode, the dark value is always zero since this part of correct needs to be done before counting*

### Non-frame-saving camera (all CCD):

CCD sensor has minimal dark current component. Therefore, in this case

    Dark_Pixel_Value = bias

-   Falcon camera: Leginon receives Falcon images after both dark subtraction and flat-field correction.

## Normalization Image (Norm image for short)

Flat field correction removes the contribution of variation in gain and artifacts on the digital camera that are reproducible, for example, the patterns of the fiber optic plate and debris fall and remain stationary on the digital camera.

Bright images record the raw image under the chosen camera configuration with the camera flooded with uniform electron beam.

Dark images and its pixel value mentioned here is the result of the calculation in the above section on dark subtraction.

Let the mean of an image be avg(Image)

Normalization_Image_Pixel_Value = [avg(Bright_Image-Dark_Image)]/(Bright_Pixel -Dark_Pixel)

Flat-Field_Corrected Image_Pixel_Value = (Raw_Image_Pixel_Value - Dark_Image_Pixel_Value) * (Normalization_Image_Pixel_Value)

Some Leginon functions requires more than one image, for example the cross/phase correlation done in drift monitoring of Drift Manager node. When the node acquires a new image that will be used to correlated to an old image, it checks the correction channel that the old image used, and force the new image to use a different correction channel. This process eliminates the origin correlation peak produced by identical noise in the two images when the same correction channel is used.

## Settings for Creating the Normalization Image

-   Instrument and Camera Configuration

Best to use an exposure time/intensity similar to the data acquisition

-   Images to combine


-   Combine method = average|median

Both methods are applied per pixel. Average is used normally. Medium is used when x-ray spikes are a common problem and requires a larger number of combining images.

-   Number of Channels = the numbers of separate normalization images that will be saved for the camera configuration.

## Settings for Image Flat-Field Correction from Another Node

-   No settings are required. If normalization image does not exist for the camera configuration, there will be no correction. Channel selection is also automatic.

## Correction by the correction plan

Correction plan is a list of bad columns, rows, and pixels that tend to give non-repeating error readings. A good example is often found at the last columns of the CCD. Because their non-repeating nature, flat-field correction can not remove their contribution.

The correction plan is associated to individual instrument, camera, and camera configuration.

-   Edit Plan = Add/Edit/Delete the bad columns/rows/pixels. Separate values by commas and pixel coordinates should be in ( ). For example, a bad pixel list may be entered as (10,20),(11,20),(11,21).


-   Grab from Image = Grab bad pixels marked in red on the image displayed.

## Intensity Clipping and Image Despike

Intensity clipping and image despike are done after flat-field correction. Intensity clipping simply replace pixel values that is outside the min/max range with the limits. Despike defines a hot pixel as a pixel that has intensity higher than the threshold multiples of standard deviation above the mean of a neighborhood box. The intensity of the hot pixel is replaced by the mean of the neighborhood box.

## Related Settings

The settings related to these two corrections apply to all camera configuration and images passed through Corrector.

-   Clipping Max | Min


-   Despike Neighborhood Size (pixel): An input of 11 gives a box of 11x11 centered at the pixel where spiking is evaluated.


-   Despike Theshold (x standard deviation above the mean of the neighborhood box (For example 11x11=121 pixels))

## Find A Single Bad Pixel

When a single pixel is defected, it may not be easy to find it on a large image, even if it changes the stats dramatically. A tool is available to help finding these pixels:

-   Leginon/Correction> Acquire either a corrected image that shows the bad stats.


-   Leginon/Correction/Toolbar> Left-click on the ![](images/stagelocations.png) button to "Add extreme points to bad pixel list". There


-   Leginon/Correction/Tools> Left-click on the "Add Region" tool that looks like "+". This adds the selected bad region to the bad pixel plan.


-   Leginon/Corrections> Acquire a corrected image in the same configuration to check if the appearance improves.

## Bad Region Correction

When a large region is covered by a fallen chip, image correction through bright/dark reference may not be sufficient to produce a spike-free image since the bright and dark values in the region are almost identical. To add such a large region into bad pixel plan, do the following:

-   Leginon/Correction> Acquire either a bright or corrected image that shows the bad region clearly.


-   Leginon/Correction> Use "Regions" target tool next to the image to enclose the bad region. The corners that the target tool identifies can be larger than the bad region but should be close to its size so that not too much is corrected.


-   Leginon/Correction/Tools> Left-click on the "Add Region" tool that looks like "+". This adds the selected bad region to the bad pixel plan.


-   Leginon/Corrections> Acquire a corrected image in the same configuration to check if the appearance improves.

[< Click Target Finder](/leginon/Leginon_Manual/Node_Descriptions/Click_Target_Finder) | [Dose Calibrator >](/leginon/Leginon_Manual/Node_Descriptions/Dose_Calibrator)
