The JAHC Hole Finder class is a variation of Hole Finder class. The purpose and operation is similar in the two node classes. The differences are 1: JAHC Hole Finder does not use edge image for correlation but the original, and 2: JAHC Hole Finder uses a scaled template image rather than a simple geometric ring for the correlation step. Like the Hole Finder, the values in this node vary so much from grid to grid (and from square to square) that the best way to find these parameters is by going through a step-by-step trial and error process. To proceed from one step of the hole targeting process to another, simply proceed from top to bottom through the display selection buttons in the image control panel. The display settings associated with each display selection are the locations where the JAHC Hole Finder parameters can be adjusted. To see the final acquisition and focus targets, enable only the Original, acquisition, and focus display selections.

**Required bindings for recieving images and publishing targets:**

previous Acquisition - (AcquisitionImagePublishEvent) -> JAHC Hole Finder
JAHC Hole Finder - (ImageTargetListPublishEvent) -> next Acquisition
JAHC Hole Finder - (QueuePublishEvent) -> next Acquisition

**Required bindings for proper waiting among nodes:**

JAHC Hole Finder- (ImageProcessDoneEvent) -> previous Acquisition
next Acquisition - (TargetListDoneEvent) -> JAHC Hole Finder

## Settings

-   Allow for user verification of picked holes = When enabled, this feature will pause and wait for the user to verify whether the correct exposure and focus targets have been selected after the Hole Finder finished processing the input image.


-   Queue up targets = When enabled, submit targets do not publish them immediately but to put them in a target list queue.


-   Declare drift when queue submitted= When enabled, force target shift correction when the queue is submitted. Useful when accurate targeting is needed.


-   Skip automated hole finder= When enabled, the automatic Hole Finder algorithm will be skipped altogether.

## Image Control Panel

NOTE: To see the effects of Testing the settings for a particular Hole Finder step in the Image Control Panel, the corresponding JAHC Hole Finder step Display must be enabled before using the Test feature in that step's Display Settings.

## Original

### Display

To view the original input image without any image processing done to it, enable this button. Enabling this button will disable/override the Edge, Template, and Threshold Displays.

### Display Settings

-   Original Image: File Entry = Enter the path and name of an MRC image that the JAHC Hole Finder can be tested on. This feature allows JAHC Hole Finder to be tested without having run a full Leginon MSI application.

## Template

The purpose of the Template step is to cross correlate a template of the properly sized template holes against the original image.

### Display

To view the Template image, enable this button. Enabling this button will disable/override the Original, Edge, and Threshold Displays.

### Display Settings

-   Use "phase | cross" correlation = to do this calculation.


-   Template Filename = Enter the path and name of a template MRC image.


-   Original Template Diameter = Enter the value in pixel.


-   Final Template Diameter = A scaled diameter in pixel. It should be chosen give the sharpest correlation peak upon testing.


-   Test = Press this button to test/apply the parameters that have been adjusted in this step.

## Threshold

The purpose of the Threshold step is to apply a threshold to the previous Template image. It is in unit of number of standard deviation above the mean. The Threshold image should have dots that represent the center of all the found holes.

### Display

To view the Threshold image, enable this button. Enabling this button will disable/override the Original, Edge, and Template Displays.

### Display Settings

-   Threshold = Enter the Threshold value of a dot that represents the center of a hole (either as absolute value or relative to the value with the stdv shown for the correlation image).


-   Test = Press this button to test/apply the Threshold to the template correlation image. Only the dots hat represent the center of the holes should appear. It is highly likely that dots not representing the center of a hole will
    also appear.

## Blobs

The purpose of the Blobs step is to begin to narrow down the "hole center dots" that have been found. This step serves as additional criteria for finding good holes.

### Display

To view Blobs, either the Original, Edge, Template, or Threshold Displays must be enabled. The Blobs that pass this step will be shown with a turquoise crosshair.

### Display Settings

-   Border = The pixel value distance from the edge of the image where all potential hole targets will be erased.


-   Max. blobs = The maximum number of hole targets or blobs at this point that are allowed. If the number of blobs exceeds this number, the extra blobs will be eliminated.


-   Max. blob size = The maximum size of a blob that is allowed to pass. This is roughly the square of an average blob diameter. Use the ruler tool on the Threshold image to determine the average diameter of a blob.


-   Test = Press this button to test/apply the Blobs criteria to the Threshold image.

## Lattice

The purpose of the Lattice step is to determine whether the blobs or "hole center dots" fit in a lattice that describes how the hole layout.

### Display

To view Lattice, either the Original, Template, or Threshold Displays must be enabled. The Lattice blobs that pass this step will be shown with a pink crosshair.

### Display Settings

-   Lattice Fitting Spacing = The distance from the center of two holes in the horizontal/vertical lattice directions (not the diagonal lattice directions).


-   Lattice Fitting Tolerance = The tolerance allowed for holes that may not exactly lie in the described lattice.


-   Hole Statistics Radius = The radius in pixels of the holes (that pass the lattice criteria) that will be used to determine each hole's statistics.


-   Hole Statistics Zero Thickness = The intensity value of an empty hole, i.e. zero thickness intensity.


-   Test = Press this button to test/apply the Lattice criteria to the result of the Blobs criteria.

## acquisition

The purpose of the acquisition step is to select holes of the proper ice thickness and arrange the desired acquisition target layout. The "focus" and "acquisition" JAHC Hole Finder steps Display Settings appear in the same window. For the purpose of this documentation to facilitate the separation of steps in the user interface, acquisition and focus will be addressed separately. Therefore, only the parameters pertaining to acquisition targets will discussed in this section. The parameters not covered in this section are part of the focus section.

### Display

To view acquisition, either the Original, Edge, Template, or Threshold Displays must be enabled. The acquisition targets that pass this step will be shown with a green crosshair.

### Display Settings

Ice Thickness Threshold:

-   Min. mean = Enter the minimum hole ice thickness value allowed.


-   Max. mean = Enter the maximum hole ice thickness value allowed.


-   Max. stdev = Enter the maximum hole standard deviation value allowed.

Target Template:

-   Use target template = When enabled, template targets will be used to compose a target list. When not enabled, the center of the hole is the default target.


-   Acquisition Target Template (Add|Edit|Delete) = Add|Edit|Delete acquisition targets that define the locations of each acquisition target. The acquisition target coordinates (x,y) are measured relative to the center of a hole. Use the
    ruler tool to determine this distance.


-   Test = Press this button to test/apply the ice thickness criteria and potentially create an acquisition target template.

## focus

The purpose of the focus step is to focus targets near selected holes. The "focus" and "acquisition" Hole Finder steps Display Settings appear in the same window. For the purpose of this documentation to facilitate the separation of steps in the user interface, acquisition and focus will be addressed separately. Therefore, only the parameters pertaining to focus targets will discussed in this section. The parameters not covered in this section are part of the acquisition section.

### Display

To view focus, either the Original, Edge, Template, or Threshold Displays must be enabled. The focus targets that pass this step will be shown with a blue crosshair.

### Display Settings

Ice Thickness Threshold:

-   Focus hole selection = Any Hole | Off | Good Hole; Select the type of Z Focus target selection. This hole will be used by Z Focus to correct stage z height when first moving to the new square.

Good Hole will select one of the good holes that passed the ice thickness test.

Any Hole will select any of the holes that passed (up until before the ice thickness test).

Off will turn Z Focus correction off.

Target Template:

-   Use target template = When enabled, template targets will be used to compose a target list. When not enabled, the center of the hole is the default target.


-   Focus Target Template (Add|Edit|Delete) = Add|Edit|Delete focus targets that define the locations of each focus target. The focus target coordinates (x,y) are measured relative to the center of a hole. Use the ruler tool to determine this distance.


-   Focus template thickness = Enter values that are used to determine whether the area where the focusing has ice that is too thick. If the ice is to thick and does not pass this ice thickness criteria, then that focus target will not be
    used. Only the first focus target that passes is used. More than one focus target can pass the focus template thickness criteria.

Use focus template thickness = When enabled, focus template targets will be checked against these ice thickness criteria.

Stats. radius = the radius surrounding the focus target that is included in the statistics measurement

Min. mean thickness = Enter the minimum ice thickness value allowed.

Max. mean thickness = Enter the maximum ice thickness value allowed.

Max. std. thickness = Enter the maximum standard deviation value allowed.

-   Test = Press this button to test/apply the ice thicness focus criteria and
    create a focus target template.

[< Hole Depth](/leginon/Leginon_Manual/Node_Descriptions/Hole_Depth) | [Manual Acquisition >](/leginon/Leginon_Manual/Node_Descriptions/Manual_Acquisition)
