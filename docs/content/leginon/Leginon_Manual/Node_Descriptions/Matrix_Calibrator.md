Matrix calibrator performs four different calibrations that based on linear transformation conversion: Image shift, beam shift, stage position, and image/beam shift

Required bindings

**Required bindings to use preset instrument configuration set by presets manager:**

PresetsManagerNode - (PresetChangedEvent) -> MatrixCalibratorNode

Matrix calibration is made by making N sets of measurements (specified by "N Average"). Each measurement set acquires three images, first at a given origin, second with an x-axis movement in the specified "Parameter" by the specified "Shift Fraction" of the image, and third with an y-axis movement by the same shift fraction. The resulting shifts in the acquired images are obtained by cross correlation. A transformation matrix is then generated for the measurement set. The origin is shifted by the "Interval" specified in the node, in meters before the next set of measurements is taken. At the end, the N matrixes obtained are averaged and saved in the database at the specific magnification and movement type and can be applied to any camera configuration. "Tolerance", expressed in fraction of image, is used as an error check. The calibration is considered failed when the measured movement is much different from that calculated from pixel calibration

Because the calibration is based on correlation of the acquired images, well contrasted images with the intended movement clearly shown but not by such a large amount that the apparent feature is altered is the key for sucessful calibrations.

Image shift calibration is useful only on FEI microscope where image shift/beam shift compensation is calibrated and stored at the scope. Without such stored calibration, Image shift/Beam shift calibration is required instead.

## Toolbar

-   Settings = Adjust the manual image acquisition parameters.


-   Acquire Image = Acquire a current image.


-   Stage Position | Image Shift | Beam Shift = Choose the type of calibration to complete


-   Parameter Settings = Adjust the parameters (and limits) for the calibration process


-   Calibrate = Start the calibration.


-   Abort = Stop the Continuous Acquire function.


-   Edit Current Calibration = Edit the matrix when the calibration is completed. Not recommended for beginner.

## Settings

-   Use "phase | cross" correlation = Select the type of correlation used to calculate the calibration.


-   Override Preset = use this node's [Instrument and Camera Configuration](/leginon/Leginon_Manual/Node_Descriptions/Presets_Manager#Parameters-Instruments) to acquire the images in this node

## Parameter Settings

-   Tolerance = percent error allowed when calculating the calibration


-   Shift Fraction = amount sequential images should shift relative to each other


-   Average = the number of sequential images that are acquired in order to calculate the calibration


-   Interval "2e-6" = the interval (m) that is used to move the stage/beam/image position to take images required for the image sequence


-   Use current positon as starting point = When enabled (default), the current stage postion is used to begin the calibration


-   Base (x,y) = If "Use current position as starting point" is not enabled, this position will be used to start the calibration

## Image Control Panel

This panel controls which image is shown in the Image Display area.

-   Image = shows the corrected images as they are acquired


-   Correlation = shows the correlation image between sequential images in a calibration


-   Peak = shows an orange crosshair over the Peak that has been identified from the correlation image

[< Matlab Target Finder](/leginon/Leginon_Manual/Node_Descriptions/Matlab_Target_Finder) | [Mosaic Click Target Finder >](/leginon/Leginon_Manual/Node_Descriptions/Mosaic_Click_Target_Finder)
