The GonModeler node models the goniometer/stage movement to give a more accurate stage position/movement calibration. The stage position is modeled in both x and y directions. For a more accurate calibration, many points or images need to be acquired to give a more accurate mathematical fit to the function. This calibration works best on a grid that will always give good cross correlations. Slot grids give large areas that can cross correlate well, but this type of grid tends to drift. Negatively stained grids or grids with a carbon in the background will work well.

*How does modeled stage position work?*

There are two types of results from doing a modeled stage calibration: 1) a function (in the form of a harmonic series) that models the mechanical behavior of the stage 2) a magnification adjustment (scaling and rotation) that allows the model function to be used at different magnifications. Part 1 needs to be done at only one magnification, because the result will be normalized in the database so that it can be used at any other magnification. Part 2 needs to be done at any other magnifications that you wish to use this calibration. The user interface of GonModeler node gives you two methods: "Fit Model" and "Mag Only" These two methods are really identical except for the final result they store in the database. "Fit Model" will store both part 1 and 2 above. "Mag Only" will onlystore part 2 (and assumes that you already have part 1 done). Since "Fit Model" is responsible for part 1, you generally need to measure a lot of points to get a good fit. You will normally select between 2 and 5 terms for the harmonic series to get a good fit. The "Mag Only" method will also fit a function to your measured points using the number of terms you specify. But the resulting best fit function is not stored in the database. Only the constant term of the resulting function is stored, because this can be used to scale the existing normalized model function to the current magnification.

Right now it is not possible to use the modeled stage calibration for building a mosaic of images. The reason is that we have not yet implemented the inverse transform of this calibration. All of the matrix calibrations are easy to invert (for instance, you can convert from a pixel shift to a stage shift, or invert that and convert from a stage shift to a pixel shift). The modeled stage calibration is more complicated to invert, so right now we can only convert from a pixel shift to a stage shift. The MosaicClickTargetFinder node is responsible for assembling the images into a complete mosaic image. It does this by looking at the stage position of each of the component images, and doing the reverse transform from stage position to pixel shift. The result is the pixel offset of the component image in the overall mosaic.

**Required bindings to use preset instrument configuration set by presets manager:**

PresetsManagerNode - (PresetChangedEvent) -> GonioMedelerNode

## Toolbar

-   Settings = set calibration, measurement, and modeling parameters


-   Acquire Image = acquire an image within this node


-   Measure = measure the distance of the latest movement


-   Play = calibrate the goniometer model


-   Abort = abort the goniometer modeling routine

## Settings

-   Use "cross | phase" correlation = to calculate the goniometer model


-   Override Preset = use this node's Instrument and Camera Configuration to acquire the images in this node


-   Measurement

## Axis: x or y = the selected axis the stage model is being measured for
 
## Points: 200 (default) = number of data points (stage movements) used
 
## Tolerance: 25 % = percentrage of error allowed in calculations
 
## Interval: 5e-06 m = interval used to incrementally move the stage to model the stage movement
 
## Label = name of the goniometer measurement (without axis suffix)

-   Modeling

## Label = name of the goniometer model (without axis suffix)
 
## Axis: x or y = axis the goniometer model is calculated for
 
## Magnification = the magnification the goniometer model is being created for
 
## Terms = 5 (default)
 
## Model magnification only = disabled (default). When enabled, the node still fit the full modeling but only the scale and the basic matrix that defines the image and stage axis relationship are stored in the database.

[< Focuser](/leginon/Leginon_Manual/Node_Descriptions/Focuser) | [Hole Finder >](/leginon/Leginon_Manual/Node_Descriptions/Hole_Finder)
