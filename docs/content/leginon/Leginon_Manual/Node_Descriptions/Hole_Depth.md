The hole depth node, is a set of tools to measure parameters needed to correlate the intensity values of hole with (I) and without ice (I0) with the physical thickness of the ice. The two intensity values gives the image contrast , c=ln(I0/I), that is used in Hole Finder Node Class as the relative measurement of thickness. Since the actual calibration of contrast against physical thickness is not yet written, we do not advise using this node unless you plan to perform your own query and fit the values with the proper function outside Leginon.

**Required bindings for recieving images:**

This node at the moment stands alone and is used in post session processing.

## Image Selection

Each selected image type are for different measurement required for the correlation.

-   I0= Image of the area after the ice is burned recorded at the magnification and defocus at which the contrast-thickness calibration is intended.

Relevent Image Control Panel-

PickHoles: Pick location and calculates mean intensity within given radius of the the Picked position.

-   I= Image of the area before the ice is burned recorded at the magnification and defocus at which the contrast-thickness calibration is intended.

Relevent Image Control Panel-

PickHoles: Pick location and calculates mean intensity within given radius of the the Picked position.

-   Hole Untilt= Image of the a small patch of ice burned away from carbob support at high magnification that is used to determine the radius of the burned cylindrical hole.

Relevent Image Control Panel-

Original: File Entry.

Edge: Create Edge Image of the hole.

Template: Create Ring Template and correlate with the edge image to obtain the radius of the cylindrical hole.

-   Hole Tilt= Image of the same area as "Hole Untilt" with the stage tilted to reveal some separation of the two cylinder end projection or partial ocluded path by one of the end projection.

Relevent Image Control Panel-

Original: File Entry.

Edge: Create Edge Image of the tilted hole.

Template: Using the tilt-projected ring template created from "Hole Untilt" and the microscopic stage alpha angle of the tilted image to correlate with the edge image to obtain the correlation peaks of the the two end of the
cylinder.

Threshold: Threshold the correlation image to reveal only the two main peaks.

Blobs: Find the two thresholded peaks and calculates the depth of the hole from the separation.

## Image Control Panel

NOTE: To see the effects of Testing the settings for a particular Hole Depth step in the Image Control Panel, the corresponding Hole Depth step Display must be enabled before using the Test feature in that step's Display Settings.

## Original

### Display

To view the original input image without any image processing done to it, enable this button. Enabling this button will disable/override the Edge, Template, and Threshold Displays.

### Display Settings

-   Original Image: File Entry = Enter the path and name of an MRC image that matches the Image selection chosen in the node toolbar. The filename and path for each type are stored separately. Only the chosen type will be displayed.

## Edge

The purpose of the Edge step is to convert the original image into an "edge" image where the edges of the holes in the image are enhanced against a black background.

### Display

To view the Edge image, enable this button. Enabling this button will disable/override the Original, Template, and Threshold Displays.

### Display Settings

-   Low Pass Filter Sigma = Enter the sigma of the low pass filter applied to the edge image. A value of 0 will not apply a low pass filter to the edge image.


-   Edge Finding Threshold = Enter a reasonable intensity value that will enhance the edges of the hole(s) in the edge image.


-   Test = Press this button to test/apply the LP sigma and Edge Finding Threshold effects on the edge image.

## Template

The purpose of the Template step is to cross correlate a template of the properly sized holes against the edge image where the edges of the holes have been enhanced in the previous step. Unlike in HoleFinder, this template is a tilt projection of the circularring.

### Display

To view the Template image, enable this button. Enabling this button will disable/override the Original, Edge, and Threshold Displays.

### Display Settings

-   Use "phase | cross" correlation = to do this calculation.


-   Rings (Add|Edit|Delete) = Add|Edit|Delete the inner and outer hole (ring) diameters in this section. Use the ruler tool while displaying the Edge image to measure the average inner and outer hole diameter. Enter the average inner and
    outer hole diameter in this section.


-   Low Pass Filter Sigma (for Phase Correlation only) = Enter a low pass filter sigma that is used only when phase correlation is used in this step.


-   Tilt Axis = Enter the angle in degree the tilt axis is measured from the y-axis of the image. Positive is counterclockwise.


-   Test = Press this button to test/apply the parameters that have been adjusted in this step.

## Threshold

The purpose of the Threshold step is to apply a threshold to the previous Template image. It is in unit of correlation. The Threshold image should have dots that represent the center of all the found holes.

### Display

To view the Threshold image, enable this button. Enabling this button will disable/override the Original, Edge, and Template Displays.

### Display Settings

-   Threshold = Enter the Threshold value of a dot that represents the center of a hole (relative to the value with the stdv shown for the correlation image).


-   Test = Press this button to test/apply the Threshold to the template correlation image. Only the dots hat represent the center of the holes should appear. It is highly likely that dots not representing the center of a hole will
    also appear.

## Blobs

The purpose of the Blobs step in Hold Depth is not only to mark the center of the thresholded image but also to calculate the depth of the hole from the two marked locations.

### Display

To view Blobs, either the Original, Edge, Template, or Threshold Displays must be enabled. The Blobs that pass this step or manually picked will be shown with a turquoise crosshair.

### Display Settings

-   Border = The pixel value distance from the edge of the image where all potential hole targets will be erased.


-   Max. blobs = The maximum number of hole targets or blobs at this point that are allowed. If the number of blobs exceeds this number, the extra blobs will be eliminated.


-   Max. blob size = The maximum size of a blob that is allowed to pass. This is roughly the square of an average blob diameter. Use the ruler tool on the Threshold image to determine the average diameter of a blob.


-   Find blobs / Calc depth= Press this button to test/apply the Blobs criteria to the Threshold image and calculate the depth of the hole if 2 blobs are found. If only 1 blob is found, the correlation peaks are considered unresolved and a separation of 1 pixel is assumed in the depth calculation.


-   Calc w/ selections= Press this button to calculate the depth of the hole using the two manually picked blobs..

## Pick Holes

The purpose of the step is to locate the burned position in either the images before or after the burning and to calculate the mean intensity within given radius.

### Display

To pick and calculate mean intensity of the Picked Holes, the Original Displays must be enabled. The acquisition targets that pass this step will be shown with a green crosshair.

### Display Settings

-   Hole Statistics Radius = The radius in pixels of the holes (that pass the lattice criteria) that will be used to determine each hole's statistics.


-   Hole Statistics Zero Thickness = The intensity value of an empty hole, i.e. zero thickness intensity.


-   Shiftpicks = If a hole has been picked and tested from I0 image, pressing this button with a I image loaded causes the current picks shift by the offset of correlation peaks between I0 to I.


-   Test = Press this button to test/apply the zero thickness and radius criteria to calculate the mean intensity of the picked hole.

[< Hole Finder](/leginon/Leginon_Manual/Node_Descriptions/Hole_Finder) | [JAHC Hole Finder (Template Hole Finder) >](/leginon/Leginon_Manual/Node_Descriptions/JAHC_Hole_Finder_Template_Hole_Finder)
