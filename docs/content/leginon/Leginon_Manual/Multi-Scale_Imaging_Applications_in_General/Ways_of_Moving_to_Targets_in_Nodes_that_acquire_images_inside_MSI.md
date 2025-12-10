Nodes that acquire images at each of the multi-scale mostly belong to a base class called Acquisition and have an icon that looks like a camera. There are many settings related to this main building block with many options for moving the received target to the detector center (targeting, in short).

Targets can be moved to the center of the detector for image acquisition using one of the
following calibrations:

-   [Image Shift](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Image_Shift_matrix_calibration)


-   [Stage Position](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Stage_Position_matrix_calibration)


-   [Modeled Stage Position](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Modeled_Stage_Position_calibration)


-   [Image Beam Shift](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Ways_of_Moving_to_Targets_in_Nodes_that_acquire_images_inside_MSI/Image_Beam_Shift_matrix_calibration)

There are two movers to chose from: Presets Manager and Navigation. Presets Manager provides
a simple one trial movement. It assumes that the move calibration is good enough to reach the
target directly. Navigation Node is more flexible, since it can be configured to perform
multiple trials. However, most of multiple movement benefit is only relevant in the case of
Stage Position/Modeled Stage Position move type. It is also not recommended to be used to
acquire images that queued targets will be selected on.

To achieve a movement of defined tolerance, movement by Navigation Node with multiple
trials checks the error of targeting after each trial move. If the error is larger than the
tolerance, the target location is recalculated from the current location, and the targeting
movement repeated. It was noticed that on FEI microscope, the movement error is lower if the
required move is smaller. Therefore this algorithm allows even a badly performed goniometer to
target accurately, at the expanse of multiple exposure in the general area. At low
magnification and highly binned short exposure, this is usually not a problem.

The settings in the Acquisition Class that determines the above tolerance is named
"Navigator Target Tolerance". You can set this setting to 0 which will turn off multiple move
option and perform the move as if it is Presets Manager.

Occasionally, the additional trials do not further reduce the targeting error due to
sluggishness of the goniometer movement. The user may want either to accept this closest
targeting or to abandon the acquisition sequence. The decision often lies in how long the
acquisition sequence is and how likely that such image with lower standard is likely to be
useful. For example, as a target for tomography tilt series, a missed target can translate to
30 min of wasted scope time. However, a slight miss that causes the target not centered but
still in the view is worth data collection effort.

The settings in the Acquisition Class that determines the above abort/proceed tolerance is
named "Navigator Acceptable Tolerance". The "Acceptable Tolerance" should always be larger
than the "Target Tolerance".

In addition, a final image shift can be applied to resulting multiple move location
although in most cases this does not improves the targeting if the targeting error is already
smaller than 1e-7 m.

[< Multi-Scale Imaging Concept](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Multi-Scale_Imaging_Concept) | [Flavors of MSI applications >](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Flavors_of_MSI_applications)
