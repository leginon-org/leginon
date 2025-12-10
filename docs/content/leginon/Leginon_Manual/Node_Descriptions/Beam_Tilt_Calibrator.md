The Beam Tilt Calibrator is in fact the calibrator for autofocus. This calibration functions well if the microscope has been well aligned first. The three main functions are defocus calibration, stigmator calibration and storage/retrieval of eucentric focus

**Required bindings to use preset instrument configuration set by presets manager:**

PresetsManagerNode - (PresetChangedEvent) -> BeamTiltCalibratorNode

## Toolbar ( Leginon/Beam Tilt Calibrator/Toolbar> )

-   Settings = Choose correlation type (phase or cross) and the CCD settings.


-   Acquire Image


-   Defocus | Stigmators = Choices of types of calibrations to perform.


-   Parameter Settings = paramters specific for calibrating the beam tilt


-   Calibrate = Begin calibrating


-   Abort = Stop the calibration processing


-   Measure = Test the beam tilt calibrations


-   Eucentric Focus From Scope = store the eucentric focus from the current microscope settings


-   Eucentric Focus To Scope = send the stored Leginon eucentric focus setting to the microscope


-   Rotation Center From Scope = store the rotation center beam tilt value from the current microscope settings


-   Rotation Center To Scope = send the stored Leginon rotation center beam tilt value to the microscope


-   Align Rotation Center = use the current autofocus calibration to align the rotation center beam tilt.


-   Edit current calibration

## Settings ( Leginon/Beam Tilt Calibrator/Settings> )

-   Use "phase | cross" correlation = choose the correlation technique that is used to
    calibrate the beam tilt


-   Override Preset = use this node's [Instrument and Camera Configuration](/leginon/Leginon_Manual/Node_Descriptions/Presets_Manager#Parameters-Instruments) to acquire the images in this node


-   Correct image for tilt=Apply cosine stretching to the image before correlating the images


-   Settling time = Wait between each beam tilt, used for testing

## Defocus or Stigmators

-   Defocus = when chosen, the beam dilt will be calibrated in order to correct the defocus


-   Stigmators = when chosen, the beam dilt will be calibrated in order to correct the stigmation

## Parameter Settings

-   Beam tilt = expressed in radian, the value gives tilt from center of the the tilt in each direction, typically 0.01. A higher number means the beam will have a larger tilt. Too large of a tilt will cause the beam to leave the CCD imaging area.


-   First defocus = in meters, typically --2e-6 m (for 50-60k x). A standard defocus used within the autofocus routine.

This value gives the first defocus from current defocus=0 point where images are acquired and correlations compared.

-   Second defocus = in meters, typically --4e-6 m ( for 50-60k x). A second standard defocus used within the autofocus routine.

This value gives the second defocus from current defocus=0 point where images are acquired and correlations compared.

## Measure

-   Beam tilt = in radian. Typically the same beam tilt used to complete the calibration (in Parameter Settings)


-   Measure = Click this button to test the defocus|stigmator calibrations

The defocus or stigmation that is measured will appear in the corresponding fields once the measurement has finished.

-   Correct Defocus | Correct Stigmator = Send the measured defocus | stigmator correction values to the microscope.


-   Reset Defocus = use this to reset the zero defocus value at the microscope

## Eucentric Focus Retrieve from /Send to scope

-   Encentric focus value needs to be saved in the database at the magnification and high tension where stage Z correction is to be made through autofocus routine.

## Rotation center Retrieve from /Send to scope

-   Rotation center beam tilt value needs to be saved in the database at the magnification and high tension where stage alpha-tilt distortion correction is to be made in the focuser node.

## Align Rotation Center

-   Align the beam tilt to the rotation center based on the current defocus/stigmator calibration.

[< BeamFixer](/leginon/Leginon_Manual/Node_Descriptions/BeamFixer) | [Beam Tilt Imager >](/leginon/Leginon_Manual/Node_Descriptions/Beam_Tilt_Imager)
