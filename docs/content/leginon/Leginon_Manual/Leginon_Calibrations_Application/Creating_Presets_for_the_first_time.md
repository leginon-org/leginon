Configuring the Presets are critical to many different applications. Presets describe
camera configurations such as image size and exposure time as well as many other microscope
parameters such as magnification and defocus. Setting presets in calibration application is
optional but recommended for determining what calibrations are needed for future runs.

## Design Presets

MSI presets can be customized to your need of data collection. By matching
nodes/subnodes in MSI with presets and move types, the behavior of the node is
defined.

See the section on [Designing Presets](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Pre-MSI_Set-up) in the chapter
for MSI application for more explanations on the presets standardized at NRAMM which we will
reference in this chapter, we use here the nomenclatures at NRAMM that is used to collect
defocus paired images with four scales of targeting ant two sequences of focusing using an
MSI application. You will need to adjust the preset parameters for your own camera, scope,
as well as the grid mesh you use.

## Presets Created for Convenience in Calibration

The table shows an example of the presets for an MSI application. For calibration
purpose, undefined image shift can be left as what received from the scope. Beam intensity,
spot size, and should be adjusted to give reasonable signal to noise ratio for usable
exposure time and for the beam to cover the whole CCD. The exact setting of exposure time
can be set later after bright and dark images are collected.

Example MSI preset initial parameters:

  Magnification:   Preset name:   Image Shift (x,y):   Binning:   Dimension:   Beam Coverage:   Exposure Time (ms):   Spot Size:   Defocus (m):
  ---------------- -------------- -------------------- ---------- ------------ ---------------- --------------------- ------------ --------------
  120              gr             as is*              8          512          max              20                    4            0.0
  550              sq             as is*              4          1024         1x CCD size      100                   4            --2e-3
  5000             hl             as is*              8          512          1x CCD           20                    4            --1.5e-4
  50000            fc             0,0                  1          512          <~ 1x CCD      300                   4            --2e-6
  50000            fa             0,0                  4          1024         >2x CCD         50                    4            --2e-6
  50000            en             0,0                  1          4096         2x CCD           170 (10e/A^2)        4            --1e-6
  50000            ef             0,0                  1          4096         2x CCD           170 (10e/A^2)        4            --2e-6

*Use whatever image shift from the microscope when the preset is newly created. These will be aligned later.

## Create Presets from microscope setting

1.  (Optional) Microscope/Reset defocus at eucentric height.
     
2.  Adjust the microscope settings at the microscope. This includes magnification,
    beam intensity, beam shift, and defocus. Beam intensity and beam shift is adjusted to
    get the good beam coverage shown in the table. Defocus only need to be
    approximate.
     
3.  Leginon/Node Selector>Select "Presets Manager" node.
     
4.  Leginon/Presets Manager> Click New From Scope icon ![](images/instrumentgetnew.png) to open "Create New Preset" setting window.
     
5.  Leginon/Presets Manager/Create New Preset> Type a descriptive name for a
    Preset, "hl" for example, left-click "Create" to save and close the window.
     
6.  Leginon/Presets Manager/Preset Parameters/Camera Configuration> Change the
    image shift, defocus, camera configuration and exposure time if necessary. It will be
    saved automatically when changed.

## Presets Selector and Cycle Order List

If Presets are not ordered as in the table above, we recommend that they are rearranged
for efficient cycling. Cycling is important for minimizing hysteresis effect on em optics
and targeting and are defaulted to be on in Presets Manager Settings. To reduce cycling
time, it is best to group the presets that often occur consecutively in order. For example,
the typical MSI preset order as in the table above.

1.  Leginon/Presets Manager> select a preset from the Preset Selector.
     
2.  Up/Down: Move the presets up or down in the Cycle Order.

## Adjusting Presets at the microscope

With cycling activated as default, the preset beam shift may behave differently from
that was first created. The following procedure check, adjust, and save the presets
parameters with cycling accounted for.

1.  Leginon/Presets Manager> select a preset from the Preset Selector.
     
2.  Leginon/Presets Manager> click To Scope icon ![](images/instrumentset.png) to send the current preset to the microscope.
     
3.  Adjust the microscope settings either at the microscope or in a node that
    controls the microscope (Instrument) and/or the camera (Navigation,etc.).
     
4.  Leginon/Presets Manager> click From Scope icon ![](images/instrumentget.png) to save the current settings to this preset.
5.  You may also adjust individual parameter of the preset through Edit Preset icon ![](images/edit.png)

## Using Presets in Calibrations

With presets created, calibrations at different magnifications can be changed by sending
the corresponding preset to the scope.

1.  Leginon/Your Calibration Node/Settings> Deactivate "Override Preset"
2.  Leginon/Presets Manager> select a preset from the Preset Selector.
     
3.  Leginon/Presets Manager> click To Scope icon to send the current preset to the
    microscope.

## Calibration Status

Calibration status of a preset is displayed in PresetsManager right below the message
log panel. This section is very useful for troubleshooting calibration problems. Over time,
certain calibrations may need to be repeated. This section will display the latest
calibration date related to the current preset.

Check this section to see which calibrations the new preset will need to be
completed.

1.  Pixel Size: This value is entered through the Pixel Size Calibrator node. (required)
     
2.  Image Shift: This is calculated through the Image Shift matrix calibration. (required)
     
3.  Stage: This is calculated through the Stage Shift matrix calibration. (Optional
    if Modeled Stage Mag Only calibration exists at the same mag).
     
4.  Beam Shift: This is calculated through the Beam Shift matrix calibration
    (Optional; Necessary to move the beam in Navigator).
     
5.  Modeled Stage: This is calculated through the Modeled Stage Position calibration
    (necessary to accurately center holes/targets for high magnification images).
     
6.  Modeled Stage Mag Only: Same function as in 5. This may be created from full or
    mag only model fit in GonioModeling.

[< Startup](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Startup_Calibrations) | [Pixel Size Calibration >](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Pixel_Size_Calibration)
