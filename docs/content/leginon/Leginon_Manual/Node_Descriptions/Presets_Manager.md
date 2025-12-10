Configuring the Presets can be critical to many different applications. Presets describe camera configurations such as image size and exposure time as well as many other microscope parameters such as magnification and defocus. Different nodes can use these predefined presets to change conditions of the microscope and CCD.

**Required bindings for using preset image shift alignment tool:**

Presets Manager - (MoveToTargetEvent) -> NavigatorNode

**Required bindings for using presets in any acquisition class (including focuser) of nodes:**

AcquisitionNodeAlias - (ChangePresetEvent) -> Presets Manager
Presets Manager - (PresetChangedEvent) -> AcquisitionNodeAlias

**Required bindings for nodes that can use preset instrument configuration set by presets manager:**

PresetsManagerNode - (PresetChangedEvent) -> Node

**Required bindings for auto dose measurement as initiated by MSI-Tomography:**

TomographyNode - (MeasureDosePublishEvent) -> MeasureDoseNodeAlias
MeasureDoseNodeAlias - (ChangePresetEvent) -> Presets Manager

## Available functions

-   Toolbar

Presets Manager Settings

-   Main Presets node panel (panel image icon)

Preset Selector

(up/down icon) Move preset up/down in the cycle order

(to scope icon) Sends parameters of the preset to scope

(from scope icon) Saves parameters of the preset from current scope and CCD settings

(acquire icon) Acquires 512x512 image at current sent preset

(remove icon) Removes selected preset from list

(align icon) Align image shift between presets

(beam shift icon) Shift beam for a preset

(new from scope icon) Creates new preset from current scope and CCD settings

(import from session icon) Imports preset(s) from another session.

Calibrations - Displays the date and time when calibrations related to the selected preset was last saved.

Parameters - Displays and Allows direct setting of parameters associate with the selected preset.

## Settings - Movement

-   Pause between preset changes

- The pause allows the optics to settle between preset changes

-   Move stage x and y axis only

- Rather than target to x,y,z,alpha, and beta settings of the goniometer, only x and y axis values are sent. Checking this selection allows eucentric height adjustment at regular interval during a long session.

## Settings - Cycle

Hysteresis of image and beam shift is experienced everyday when using the microscope. This general hysteresis affects many Leginon calibrations. Keeping current in the lenses, particularly the objective lens, has been seen to help reduce the effects of this hysteresis. Likewise, stepping through magnifications in a fixed order (low to highest to low to highest etc.) has been empirically helped reducing the hysteresis effects.

It is highly recommended to leave the first two check boxes in this section (Leginon/Presets Manager/Settings) enabled. Cycle Magnification Only should be checked if the hysteresis from changing beam intensity is negligible.

-   Cycle presets

- The presets' cycle Order will be used whenever changing between presets.

-   Optimize Preset Cycle

- If there are multiple presets with the same magnification in the Cycle Order, only the first preset in the order list or the destined preset will be sent. This helps speed up the cycling time. Use of this option assumes that the main source of hysteresis is change of magnification.

-   Cycle Magnification Only

- Other than the case for the final destination preset, only the magnification will be sent to the microscope instead of all the other preset's parameters. All of the destined preset's settings will be sent to the microscope. This option will reduce the cycle time as well. Use of this option also assumes that the main source of hysteresis is change of magnification.

## Presets Selector and Cycle Order List

-   Leginon/Presets Manager> select a preset from the Preset Selector.


-   Up/Down: Move the presets up or down in the Cycle Order.

NOTE: To reduce cycling time, it is best to group the presets that often occur consecutively in order. For example, the typical MSI preset order is

[ gr, sq, hl, fc, fa, en, ef ]

## Sending Presets to the microscope

-   Leginon/Presets Manager> select a preset from the Preset Selector.


-   Leginon/Presets Manager> click To Scope icon to send the current preset to the microscope.

## Adjusting Presets at the microscope

-   Leginon/Presets Manager> select a preset from the Preset Selector.


-   Leginon/Presets Manager> click To Scope icon to send the current preset to the microscope.


-   Adjust the microscope settings either at the microscope or in a node that controls the microscope (em*) and/or the camera (navigator,etc.).


-   Leginon/Presets Manager> click From Scope icon to save the current settings to this preset.

## Acquistion / Dose Image

This section is used to acquire a "Dose Image" and calculate the electron dose per area on the specimen at the current preset using the averaged intensity of the image and various calibrations. The dose value is then updated in the database for the current preset. To acquire a dose image, no object must obstruct the path of the electron beam.

The dose calculated by this function relies on the camera sensitivity calibration obtained in the [Dosecal](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Dose_Camera_Sensitivity_Calibration) node as well as the [pixel size calibration](/leginon/Leginon_Manual/Node_Descriptions/Pixel_Size_Calibrator). The result of the calibration is CCD sensitivity value that converts number of electrons to camera signal count (i.e. intensity).
With both information, the average CCD intensity of the Dose Image acquired through the Presets Manager can be used to calculate the dose in unit of electrons per angstrum. Change of preset scope parameters will reset the dose value.

-   Move the stage to an empty area or a broken hole so that the whole screen can have uniform illumination.


-   Leginon/Presets Manager> Send a selected preset and its parameters to scope.


-   Leginon/pm/Presets Manager> click Acquire Dose Image.

The image and the calculated dose will be display.

In order to reduce the acquisition time, the dose image has a maximal dimension of 512x512 and is centered at the same position as the camera configuration of the preset.

The rest of the preset's settings (e.g. Camera Binning, Exposure Time, Beam shift, Intensity, etc.) are unchanged during the dose image acquisition.

Exposure time can be changed automatically by matching a desired dose.

## Removing a Preset

-   Leginon/Presets Manager> select a preset from the Preset pull-down list in the Selection section.


-   Leginon/pm/Presets Manager> click Remove icon.

## Align Presets To Each Other

To align presets by image shift, first a global reference is chosen. The global reference serves two purposes. First as the parking preset that the scope returns to after acquiring images at various mags. Second as the preset for initial alignment. The automatic sequence centered at the magnification of the global reference First it aligns pairs of
magnification towards higher and higher magnification for those at higher magnification than the global reference and then toward lower and lower magnification for those at lower magnification than the global reference.

For each magnification, a preset is automatically chosen to be used in the alignment and is displayed in the window. The left panel displays the reference preset and the right panel displays the preset to be aligned. Navigate on the reference image moves the stage while navigate on the align image moves image shift.

The image shift is saved at each move to the specified preset but not other presets of the same magnification until "continue" is clicked.

To switch to custom alignment between arbitrary presets, change the preset assigned for either panel when the window is first open.

## Shift beam for a preset

## Create Presets from the current Session

-   Adjust the microscope settings either at the microscope or in em* node or any node where camera configuration can be set)
    Aliased as instrument in most applications).


-   Leginon/Presets Manager> Click New From Scope icon to open "Create New Preset" setting window.


-   Leginon/Presets Manager/Create New Preset> Type a descriptive name for a Preset, "hole" for example, left-click "Create" to save and close the window.


-   Leginon/Presets Manager/Parameters/Camera Configuration> Change the camera configuration and exposure time if desired. It will be saved automatically when changed. This step is necessary sometimes because the preset is created with the current camera configuration at the CCD.

## Import Presets from a previous Session

-   Leginon/Presets Manager> select (import preset icon) to open the import presets window.


-   Leginon/Presets Manager/Import Presets> select the session from which the presets will be imported in the pull-down list. Only sessions from the same instrument used in the current session will be displayed.


-   Leginon/Presets Manager/Import Presets> select the presets to be imported, import them and then press done to exit the window. You can select all presets by highlighting all presets (select the first preset with left click, and then select the last preset with shift-left click).

## Calibration Status

This section may prove to be very useful to troubleshoot calibration problems. Over time, certain calibrations may need to be repeated. This section will display the latest calibrations that were completed for the settings the current preset has and when they were completed.

If a new presets needs to be created. Then after creating the new preset, check this section to see which calibrations the new preset will need to be completed.

-   Pixel Size: This value is entered through the Pixel Size Calibrator node. (required)


-   Image Shift Matrix: This is calculated through the Image Shift matrix calibration. (required)


-   Stage Shift Matrix: This is calculated through the Stage Shift matrix calibration. (necessary to build an Atlas).


-   Beam Shift Matrix: This is calculated through the Beam Shift matrix calibration (necessary to move the beam in Navigator).


-   Modeled Stage: This is calculated through the Modeled Stage Position calibration (necessary to accurately center holes/targets for medium magnification images).

## Preset Parameters

Access Preset Parameters through edit preset ![](images/settings.png)

## Instrument Selection

Select the instruments available on the scope client

-   TEM


-   CCD Camera

## CCD settings

-   Common Configuration - choose one of the common configurations (dimension x binning). All of these configurations use the center portion of the CCD.


-   Or, use Manual camera configuration settings.

Common Configuration> choose Manual

Enter the image Dimension (x,y).

- Pay attention to the binning and offset to ensure the proper actual coverage of the CCD.

Enter the image Binning (x,y).

Enter the offset from the top left hand corner of the CCD. Remember to check that the Dimension, Binning, and Offset are set to values to make sense (i.e. do not enter 4096x4096 dimension, 4x4 binning, 512x512 offset for a 4k
CCD).

-   Camera Configuration> Enter the Exposure Time (in milliseconds).

## Microscope settings

-   magnification


-   defocus (in meters)


-   spot size (1-11)


-   intensity (0.0-1.0)


-   image shift (in meters)


-   beam shift (in meters)


-   Pre-exposure (s): Lowers the main screen for the given time as a pre-exposure before image acquisition


-   Dose-Displays the dose estimate from the most recent dose image acquired with current preset parameters. This value has the units of # electrons / (Angstrom)^2. If the dose image has not been acquired for this preset, 0.00000e+0.0 is the
    default

## Film settings

An exposure onto film can be done instead of acquiring an image with the CCD. To acquire an image onto film, simply enable the "film" checkbox:

## Energy Filter settings

If EFTEM is on, and if "Energe Filtered" is checked, the energy filter will be set to a width of the specified value when the preset is sent to the scope

[< Pixel Size Calibrator](/leginon/Leginon_Manual/Node_Descriptions/Pixel_Size_Calibrator) | [Raster Finder >](/leginon/Leginon_Manual/Node_Descriptions/Raster_Finder)
