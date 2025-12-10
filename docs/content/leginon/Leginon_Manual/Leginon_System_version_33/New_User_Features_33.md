## [FEI Volta Phase Plate Integration](/leginon/Leginon_Manual/Leginon_System_version_33/New_User_Features_33/Volta_Phase_Plate_Usage)

Automated control of hole-free Volta phase plate from FEI, including switching to the next patch, pre-charging, and procedure we use to evaluate phase plate installation.

## [Leginon "MSI-T-Tilt" Application](/leginon/Leginon_Manual/Leginon_MSI-T-Tilt_Application)

Application to make collecting large set of tilted images easier as described in Tan et. al. Nature Methods 14, 793--796 (2017) doi:10.1038/nmeth.

## [Ice Thickness Measurement using Energy Filter](/leginon/Leginon_Manual/Leginon_System_version_33/New_User_Features_33/Ice_Thickness_Measurement_using_Energy_Filter)

New node, IceT, to measure ice thickness automatically by taking extra images with and without slit inserted and using measured MFP. Requires energy filter. Can add to all apps which have AlignZLP.

## [Slack notification for Leginon errors](/leginon/Leginon_Manual/Leginon_System_version_33/New_User_Features_33/Slack_notification_for_Leginon_errors)

-   General time out and error notification with Slack

## General Features

### Target Finder:

1.  Option to force user to add focus target: This feature is default to require focus targets but can be set to "Do not require focus targets in user verification" in advanced settings dialog in any Target Finder.
2.  [Multiple Hole Template generation](/leginon/Leginon_Manual/Leginon_MSI-T_Application/Exposure_Targeting_Set-up_for_MSI-T_for_Four_holes/New_Exposure_Targeting_Set-up_in_MSI-T_for_Multiple_holes).
3.  Using Focus hole selection option with an offset. Useful when the edge of the hole is needed to perform autofocusing.
4.  Option to allow multiple focus targets to be submitted. The result is an average of the focus results at different position.
5.  Option to define minimal hole stats standard deviation.
6.  Red square next to the node name Indicates that settings chosen by the user currently are such that tree-depth traversal automated data collection would be hindered. For example, "Allow user verification" is turned on.

### Refinement of the behavior of Reference nodes such as "Align ZLP"

1.  Add a reference target from a Reference Node at the center of the image acquired that can be more accurately moved to with iterative move by Navigator. (Need to use new MSI applications).
2.  Set settle time after Leginon is moved back from the reference target.

### Enforcing dark current image acquisition.

1.  Automatically acquire and update hardware dark current image on K2 camera while "N2 filling" is running.
2.  Automatically acquire and update hardware dark current image on K2 camera for acquiring Bright reference image.

### Tomography

1.  Aternating tilt sequence
2.  Option to use the preset exposure time at all tilts and thus ignore dose adjustment.

### Focuser

1.  [Option to use diagonal beam tilts for phase plate data collection](/leginon/Leginon_Manual/Leginon_System_version_33/New_User_Features_33/Special_Beam_Tilt_Calibration_for_Phase_Plate)
2.  Not to recheck drift until it passes at first time. Such was the default behavior but tend to delay stabilization since the first measurement always shows higher drift from beam induced movement.

### Stage alpha tilt stability enforcement.

This is added because the goniometers on some scope slips in the way that the position reached is always larger than the requested angle, causing the tilt angle drifts over time. The stage tilt is enforced in

-   Grid Targeting Node Settings
-   Turn on the advanced settings "Tilt the stage like its parent image" in all Acquisition node class if the tilt needs to be preserved.

### Image rotation and scale modification calibrations

-   For highly defocused image that has introduced rotation and size change of the image.

### Some TEM remote control in Leginon (in development) See [here](/leginon/Leginon_Manual/Node_Descriptions/TEM_Controller) for required binding. You can add it to any MSI application.
