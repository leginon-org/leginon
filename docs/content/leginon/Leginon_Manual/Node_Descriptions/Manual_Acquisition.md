Manual Acquisition is a node that allows the electron microscopist to acquire CCD images manually while at the microscope. This node essentially creates a button to acquire images manually with Leginon and gives all the benefits of the Leginon database and image storage.

Required bindings: None

## Toolbar

-   Settings = Adjust the manual image acquisition parameters.


-   Grids = Select the current grid.(Not used without Project Database)


-   Acquire = Acquire a current image.


-   Continuous Acquire = Click this to begin acquiring images continuously.


-   Abort = Stop the Continuous Acquire function.

## Settings

-   Camera Configuration = Select the parameters that describe how the image is acquired.

Dimension = image x,y pixel dimension

Offset = x,y offset from top left corner of full CCD image

Binning = x,y image binning

pre-configured image sizes

Custom = customize image dimension, offset, and binning

Exposure time (ms) = CCD and specimen expsosure time

-   Correct image = When enabled, the raw CCD image will be corrected with Bright and Dark CCD reference images


-   Save image to database = When enabled, the acquired CCD image will be automatically stored in the database. All microscope and camera information will be stored for each image.


-   Loop pause "30" seconds = The amount of time the Continuous Acquire function waits before acquiring the next image.


-   Label = Enter a label to be inserted in the image file name (in addition to the normal Leginon file name).*


-   Main Screen: Up before acquire = When enabled, Leginon will raise the microscope's main viewing screen.


-   Main Screen: Down after acquire = When enabled, Leginon will lower the microscope's main viewing screen after an image has been acquired.


-   Low Dose:

- Use low dose = When enabled, Leginon will switch the microscope from focus to exposure mode of the Low Dose kit to acquire the image and then return to focus mode.

- Low Dose pause "4" seconds = Wait this amount of time before acquiring an image when using Low Dose on the microscope and acquiring images with the Acquire feature in this node. Increase the time if the microscope does not change modes fast enough.

[< JAHC Hole Finder (Template Hole Finder)](/leginon/Leginon_Manual/Node_Descriptions/JAHC_Hole_Finder_Template_Hole_Finder) | [Matlab Target Finder >](/leginon/Leginon_Manual/Node_Descriptions/Matlab_Target_Finder)
