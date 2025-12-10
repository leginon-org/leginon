## [Gatan K2 Summit support](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Gatan_K2_Summit_Support)

* Acquire summed frame counted, super-resolution, or linear mode image thru Leginon
* Trigger raw frame saving
* [Transfer raw frame images off hard drive of K2 during data collection to a network drive](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Direct_Electron_DE-12_direct_detection_device_support/DDD_raw_frame_file_transfer).
* [Compile gain corrected movie stack thru Appion](/leginon/appionGainDark_correction_of_the_raw_frame_with_or_without_drift_correction)

## Microcondenser mode setting in presets manager

## Target Navigation:

1.  Option of using parent image move type to move to target during target adjustment.
    -   This improves the targeting accuracy and minimize image-shift-induced beam-tilt in image-shifted final exposure if queuing is used in Exposure Targeting and Navigator iterative move is used in acquiring its parent image.
    -   Activate it at /Leginon/Exposure/Settings/Advanced Settings: Use ancestor image mover in adjustment

## Automatic Target Finding:

1.  Limit number of focusing performed on a series of images.
    -   For example, focus once every 5 hl images that processed by Exposure Targeting node.
    -   Iterator is reset at new parent so that hl image from a new square will always be focused.
    -   Activate at /Leginon/Exposure Targeting/Settings/Advanced Settings/Hole Finder(or Raster Finder) Settings: Focus every nnn image. Default=1 meaning no skipping.
2.  Option to threshold very low intensity part of the image (grid bar or thick contaminant before template correlation in JAHCFinder used in MSI-T application
    -   This has the effect of reducing false-positive in template-based hole finding.
    -   Enter the threshold value at /Leginon/Exposure(or Hole) Targeting/Template Correlation Settings: Fill image values below n with mean before correlation.

## Focusing

1.  Repeat same beam-tilt-based focusing step with the exactly same setting except not to drift checking will improve the focusing when the first adjustment is large
    -   The first focusing step brings the defocus close to the range ideal for the algorithm for the repeat.
    -   A bug fix makes this approach reliable and is recommended if defocus is really critical and speed of data acquisition does not out-weight it.

## RCT Acquisition:

1.  Tilt Test Tool ![](images/alpha.png)
    -   Usage: For testing if the grid bars will block the intended targets when tilted.
        # Send the preset using for defining the RCT targets to scope with Presets Manager.
        # Each click of the Tilt Test Tool will take the goniometer to the next tilt defined in RCT settings and acquire an image.
