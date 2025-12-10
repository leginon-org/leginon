## Graphical User Interface

-   A basic settings dialog with typical user interacting items is presented to the user first. The complete dialog is available by clicking "Advanced" button in there.

## Targeting Accuracy

-   We have modified the image-shift targeting method so that the accuracy of the targeting improved significantly between parent images at M mode and target images at SA mode. The change is transparent to the user and requires image-shift calibration at both presets used.

## Acquisition Node

-   Background reading is available for low-magnification, large area rastering. This does not work well with high resolution requirement, but provides a significant speed-up for use with MSI-Section type of application.


-   The column valve (and emission turned off, if so chosen) can be automatically closed after target queue is exhausted by clicking the "Toggle Queue Timeout" button once the queue processing has started.


-   Leginon can send you an e-mail, pause or abort the target list if the image intensity is too high or too low.


-   Beam tilt induced by image shift can be corrected if calibration is made (Experimental).

## TargetFinder Node and its subclasses

-   Right click on a target while Shift key is pressed down clears all targets of the same selected type.


-   Right click anywhere on the image while Shift and Ctrl keys are pressed down clears all targets on the image.

## JAHCFinder Node (used in MSI-T)

-   Blobs can be manually selected.


-   Lattice can be extended to cover the whole image or to a 3x3 pattern, based on two blob selections, first as the center of the extension, second to define the lattice spacing and rotation.

## Corrector Node

-   Gain correction is now handled by corrector client behind the scene. The normalization and dark images used for each correction is recorded in the database so that it can be decorrected in the future if necessary.


-   Despiking option and parameters are relocated into image plan editing dialog and are set separately for each camera configuration.

## Beam Tilt Calibrator Node

-   Automated coma-free alignment can be done once calibrated in the same node.

## [Beam Tilt Imager Node](/leginon/Leginon_Manual/Node_Descriptions/Beam_Tilt_Imager)

-   Acquiring Zemlin Tableau for coma-free alignment. Manual correction of the beam tilt can be done by interacting with the displayed tableau, too.

## Tomography Node

-   optional Saxton scheme of tilt series collection


-   option for using the last z0 value of the model for initialization. Useful when Tomo Focus node consistently give an offset in z in comparison with the backlash corrected value found through tomography node.

## MSI-Section3step application

-   capable of collecting tilt groups as well.

[< PyScope Changes](/leginon/Leginon_Manual/Version_Change_Log/Leginon_System_version_20/PyScope_Changes_20) | [New Web Tool Features >](/leginon/Leginon_Manual/Version_Change_Log/Leginon_System_version_20/New_Web_Tool_Features_20)
