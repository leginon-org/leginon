MSI-T PP Application and its two-client version MSI-T2 PP are designed for phase plate workflow.

1.  Use [Application administration](/leginon/Leginon_Manual/Administration_Tools/Applications) myamiweb tool to import from _your-myami-git-clone_/leginon/applications/MSI-T2_PP.xml
2.  Run this at *your-myami-git-clone* to import the default settings for the new nodes
        python dbschema/tools/import_leginon_settings.py MSI-T_PP

## Set up AutoIt. See Issue #3786 for example script download.

## [Special Beam Tilt Calibration for Phase Plate](/leginon/Leginon_Manual/Leginon_System_version_33/New_User_Features_33/Special_Beam_Tilt_Calibration_for_Phase_Plate)

## Node Settings

MSI-T PP is different from typical MSI-T in several ways mainly to avoid image shift in exposure and to reduce on-plane condition hysteresis by not going to lower mag and/or large defocus after multiple beam-tilt based autofocusing.

1.  **PP Exposure** is set to move to the target by stage position. There is no drift adjustment
2.  **PP Focus** has an active option that [performs beam tilt in a diagonal direction](/leginon/Leginon_Manual/Leginon_System_version_33/New_User_Features_33/Special_Beam_Tilt_Calibration_for_Phase_Plate)
3.  Extra step of hole centering aimed to minimize the movement required in target processing in **PP Exposure** node. This is done with navigator move in **PP Hole**, and fixed target position at the center of the parent image in **PP Exposure Targeting**.

-   The steps from Grid Targeting* to **Hole** is similar to other MSI applications. Queuing at **Hole Targeting** works well and a focus target should be chosen for use in **Z Focus** node.
-   **PP Hole Targeting** should not include focus target. Set it up for single hole centering, or multi-hole centering if **Hole Targeting** were not overlapping but contained multiple holes. O.K. to queue.
-   **PP Exposure Targeting** must not use queuing to reduce large change in condensor lens current. Set up as fix targets with acquisition target. The default settings set the acquisition target at the center of the image to avoid actual movement. You may need to adjust the position of the focus target or add multiple focus targets if extra accuracy in defocus is required. Their focus results will be averaged.


-   **Phase Plate** node settings allow you to set the number of **PP Exposure** counts before it switches automatically, as well as how long you want to activate the new patch by beam exposure. See [How often should the phase plate moved to the next patch\ ](/leginon/Leginon_Manual/Leginon_System_version_33/New_User_Features_33/How_often_should_the_phase_plate_moved_to_the_next_patch_). You should also set the activation time for focus spot. Focusing spot activation makes increases the contrast of the auto-focus images. 5 seconds should be enough.

See [Phase Plate Aligner Tool Bar](/leginon/Leginon_Manual/Leginon_System_version_33/New_User_Features_33/Volta_Phase_Plate_Usage/Phase_Plate_Aligner_Node_Class/Phase_Plate_Aligner_Tool_Bar) for other functions of the node.

## Operation

1.  Set beam to on-plane condition at a previously used phase plate position. **VERY IMPORTANT** Use the same beam settings and defocus for en, fa, fc presets. --0.5 um defocus is typical. You may offset it by Cs of your TEM. For example, use --0.3 um if your Cs is 2.0 mm.
2.  Open Settings dialog in **Phase Plate** node, enter the current phase plate slot number (base 1), and the phase plate patch number. Click **Update** to register.
3.  Test a few exposure throught the flow on the old phase plate patch before advance to clean phase plate patch with the green arrow in **Phase Plate** tool. The exposure should also be reset.

_

[< Special beam tilt calibration for phase plate](/leginon/Leginon_Manual/Leginon_System_version_33/New_User_Features_33/Special_Beam_Tilt_Calibration_for_Phase_Plate) | [Phase plate activation timing >](/leginon/Leginon_Manual/Leginon_System_version_33/New_User_Features_33/How_often_should_the_phase_plate_moved_to_the_next_patch_)
