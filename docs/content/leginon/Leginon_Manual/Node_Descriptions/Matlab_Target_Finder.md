The Matlabe Target Finder node behaves like other target finding nodes in that it takes images as input and outputs a list of targets. In this case, Leginon sends the image to an externally running Matlab process, which then sends the list of targets back to Leginon.

In order to use the Matlab Target Finder, you must:

-   have matlab installed on the machine where the node will run
-   have the mlabwrap python module installed. See http://sourceforge.net/projects/mlabwrap/

In addition to the usual target finder settings, this node needs to be configured with the matlab function (.m file) that should be executed on the image. The function should take the image as input in the form of a two dimensional array. The output should be two arrays, one for focus targets and one for acquisition targets. Each is an array of x,y pairs. Here is a simple example where the function generates a constant set of targets for any input image:

*example Matlab module for target finding*

    function [acquisition, focus] = example(image)
    acquisition = [168, 234; 203, 54; 450, 390]
    focus = [324, 42; 36, 248; 151, 94]


This generates three acquisition targets and three focus targets. Leginon will display the targets on the image and optionally allow the user to edit the targets before submitting them.

**Required bindings for receiving images and publishing targets:**

previous Acquisition - (AcquisitionImagePublishEvent) -> Hole Finder
Hole Finder - (ImageTargetListPublishEvent) -> next Acquisition
Hole Finder - (QueuePublishEvent) -> next Acquisition

**Required bindings for proper waiting among nodes:**

Hole Finder- (ImageProcessDoneEvent) -> previous Acquisition
next Acquisition - (TargetListDoneEvent) -> Hole Finder

## Settings

-   Allow for user verification of picked holes = When enabled, this feature will pause and wait for the user to verify whether the correct exposure and focus targets have been selected after the Hole Finder finished processing the input image.


-   Queue up targets = When enabled, submitting targets do not publish them immediately but to put them in a target list queue.


-   Declare drift when queue submitted= When enabled, the node forces target shift correction when the queue is submitted. Useful when accurate targeting is needed.


-   Matlab Module File = the entry defines the Matlab script file used in the target finder.

## Image Control Panel

NOTE: To see the effects of Testing the settings for a particular Hole Finder step in the Image Control Panel, the corresponding Hole Finder step Display must be enabled before using the Test feature in that step's Display Settings.

## Image

### Display

To view the original input image, enable this button.

### Display Settings

-   Test Image: File Entry = Enter the path and name of a MRC image that the Matlab Target Finder can be tested on.

## acquisition

In Matlab target finder, the purpose of the acquisition setting is only for display and user selection.

### Display

To view acquisition, the Image Display must be enabled. The acquisition targets that the finder chooses will be shown with a green crosshair.

## focus

In Matlab target finder, the purpose of the focus setting is only for display and user selection.

### Display

To view focus, , the Image Display must be enabled. The focus targets that the finder chooses will be shown with a blue crosshair.

[< Manual Acquisition](/leginon/Leginon_Manual/Node_Descriptions/Manual_Acquisition) | [Matrix Calibrator >](/leginon/Leginon_Manual/Node_Descriptions/Matrix_Calibrator)
