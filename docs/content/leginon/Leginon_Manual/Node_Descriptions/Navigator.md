The Navigator node is quite useful because it allows the user to test many of the calibrations that have been completed, such as image shift, beam shift, stage position, modeled stage position, and dose measurements (indirectly). Additionally, Navigator could be used to simply navigate across the grid in the microscope using Leginon calibrations and
acquire images directly. A iterative stage movement requested by Acquisition Node Class is also possible.

**Required bindings to use preset instrument configuration set by presets manager:**

PresetsManagerNode - (PresetChangedEvent) -> NavigatorNode

**Required bindings to use Navigator to move to a target (iteratively) by Aquisition node class:**

AcquisitionNode - (MoveToTargetEvent) -> NavigatorNode

## Navigate using a calibration

A particular calibration, "stage position, image shift, modeled stage position, or beam shift," can be chosen to navigate across the grid (or the current image in Navigator). The "beam shift" calibration will center the beam. While using the "beam shift" TEM parameter option, try to double click towards the center of the beam (that is displayed in the CCD imaging area). The new image will try to center the beam around the point where the mouse was double clicked.

-   Leginon/Navigator> click Acquire


-   Leginon/Navigator> select the TEM Parameter (the calibration to test)

Available calibrations (these calibrations are only available if they have been completed):

[Stage Position](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Stage_Position_matrix_calibration)

[Image Shift](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Image_Shift_matrix_calibration)

[Modeled Stage Position](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Modeled_Stage_Position_calibration)

[Beam Shift](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Beam_Shift_matrix_calibration)

-   Leginon/Navigator> Target to one area by double left clicking

The feature that is double clicked will be centered in the image. If the feature is not centered in the new image, then the calibration needs to be repeated or the microscope has been altered in some way.

## Iterative Move Navigation

Navigation, especially navigation by stage position movement, has error that is larger at larger moving distance. Therefore, the accuracy of the navigation by stage movement can be improved by multiple moves. By specifying the tolerance of the navigation error, Leginon can achieve more accurate navigation. This feature is activated by giving a non-zero value for "Move to within xx m of clicked position" within Navigator for direct click-and-move or from an Acquisition node class that uses Navigator as the mover.

## Calibration Assessment

Calibration Error Checking can calculate and display how much error there is between the targets that were selected and how accurate the selected calibration moved to that target.

-   Leginon/Navigator> enable the Calibration Error Checking checkbox.


-   Leginon/Navigator> select the TEM Parameter (the calibration to test)


-   Leginon/Navigator> click Acquire


-   Leginon/Navigator> Target to one area by double left clicking


-   Leginon/Navigator> Result will show how much error there was between what was selected and what the image actually shows.

## Save and Restore Stage Locations (Tool Icon: ![](images/stagelocations.png))

Save (x, y) stage positions in the Stage Locations section to later revisit the same positions. Keep the From Scope gets X and Y Only check box enabled, otherwise the z will also be recorded (this is most probably not useful for later checking).

*Save a new location:*

-   Leginon/Navigator> enter a New Name (for the postion that will be saved).


-   Leginon/Navigator> enter a New Comment.


-   Leginon/Navigator> click New Location From Scope (to save the current stage position).

- The new saved location will appear in the Location Selector.

*Go to a saved location:*

-   Leginon/Navigator> select a location (from the Location Selector).


-   Leginon/Navigator> click To Scope

*Update / Remove a saved location:*

-   Leginon/Navigator> select a location (from the Location Selector).


-   Leginon/Navigator> click From Scope (to update) or Remove (to delete the
    location).

## Settings

-   Check Move Error = Use correlation to find the actual shift of images before and after navigation and compare that with the expected shift value according to the calibration used.


-   Wait time after shift = Settling time after the navigation before image acquisition.


-   Override Preset = use this node's [Instrument and Camera Configuration](/leginon/Leginon_Manual/Node_Descriptions/Presets_Manager) to acquire the images in this node


-   Local Correlation Size (pixels) = The images are cropped before correlation to a square box of this size around the intended target on the original image and the same around the center of the image after the move. Such cropping limit the correlation peak in a expected distance. This setting is the only navigation settings that also applied to all MoveToTarget request from other nodes.


-   Move to within "xx" m of clicked position = The tolerance for iterative movement.

[< Mosaic Target Maker](/leginon/Mosaic_Target_Maker) | [Pixel Size Calibrator >](/leginon/Leginon_Manual/Node_Descriptions/Pixel_Size_Calibrator)
