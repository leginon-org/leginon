The following sections will describe how to operate the MSI application once set-up is complete. MSI operation can vary depending on the quality of the specimen in the microscope and how well the calibrations have been completed. Once squares are manually picked from the atlas, the entire acquisition process is capable of proceeding without human intervention. This sort of hands-off operation does depend on how well holes can be found in the images of squares and how well high magnification exposure and focus targets can be picked in the the image of a hole. If the stage is drifting, the Drift Monitor will not allow acquisition to continue until the drift has settled down. Manual intervention in the acquisition process can make the hole finders operate better. Manual check before and after the autofocus routine runs is also possible in the Focus node. Manually checking after the autofocus routine finishes is a way for the Leginon user to verify that the autofocus routine worked properly.

If the computer does not have a lot of memory, it is recommended that Leginon should be the only application running on the computer during an experiment because all the imaging and processing take up a lot of memory.

## Start Leginon and MSI (if not already started)

1. local> start-leginon.py

2. Leginon Session> log in and select "Create session" if a new session is needed.

Create Session> Fill in needed information such as session name and comments. Select instrument and project, if project database is used. Image path is automatically selected.

3. Leginon Session> Select the session you have just created or use a previous session to start.

4. Leginon/Application/Run> Select the "MSI" application, the scope, and the local launcher. Click Run.

## Reload the Atlas (Only if Leginon is being restarted)

**Important**
The Atlas should have already been created by following the [MSI everyday set-up checklist](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_Quick-start).


**How to reload atlas:**

This is used if Leginon was stopped and restarted.

1. Leginon/Square Targeting/Mosaic ![](images/atlasmaker.png)> Enter the size of the mosaic atlas loaded into the image display for better resolution. For example, Scale image to: 2048 for more resolution, 512 for fast loading

2. Leginon/Square Targeting/Tiles ![](images/tiles.png)> Select the atlas label in "Load tiles from mosaic." The most recent one is the default.

3. Leginon/Square Targeting/Tiles> Click "Load"


## Select Squares on the atlas

Pick squares to collect data from by making selections on the atlas.

1. Leginon/Square Targeting> Refresh the target display by clicking ![](images/refresh.png).

2. Leginon/Square Targeting> Click the "acquisition" selection button ![](images/arrow.png).

3. Navigate around the atlas to find suitable squares for acquisition.

[Setup Auto Square Finder using example targets](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_Operation/_Setup_Auto_Square_Finder_using_example_targets)

This step is purely empirical at this point (by eye). If using Quantifoil grids with ice, look for squares that have holes paler than the surrounding carbon. Although Leginon has automatic algorithm for square finding, the adjustment of parameters takes more time than what human can accomplish easily. Use the zoom to look at the holes more closely. Note that the zoom will take a long time on such a large image. Therefore...

NOTE: Be sure to be patient when clicking the zoom button, otherwise Leginon will
take a while to catch up to the number of zooms that have been asked for.

4. Click on squares that will be acquired.

* red cross hair = previously targeted or "done" squares.

* green cross hair = new targets

* orange cross hair = current position (updated by pressing the Leginon/Square Targeting> Refresh button ![](images/refresh.png))

5. Once all the targeted squares have been selected, click "Submit Targets."

6. Leginon will indicate where the next step is by showing active green icons next to the nodes that are being used. A question mark icon will appear when Leginon requires user interation. The message log for each node indicates what is happening that particular node.

## Select Holes on the first image of a square

Pick holes to collect data from by making selections on the first image of a square.

1. Leginon/Hole Targeting> Check whether holes were selected (acquisition targets = green crosshair, focus target = blue crosshair).

2. Edit the targets by mouse left click (add) or right click (delete) on the target in the image viewer with the picking tool for the target type active.

3. If the hole selection is acceptable, uncheck "Allow for user verification of picked holes" in Leginon/Hole Targeting/Settings>.

4. If the hole selection is not acceptable, try adjusting the Hole Targeting node to find holes in the current image of a square. Refer to the [Hole Targeting Set-up](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Hole-Targeting-Set-up).

5. Click "Submit Targets"

## Manually check focuser that uses Stage Z as the correction method

Manually checking the focus after eucentric focusing of hl images is recommended for bent grids.

1. When the Manual Focus window opens automatically (when Leginon reaches the Z Focus node), click "Eucentric focus to instrument" !http://emg.nysbc.org/software/leginon/images/icons/instrumentset.png. The rings of the CTF in the FFT should disappear if it is looking at the carbon support using fc preset. If hl preset is used to look at a hole during manual focus, look for the loss of contrast in IMAGE.

2. Adjust "Stage Z" until the image appears to be focused if not already so. Use a large step such as 5e-6 m.

3. If the defocus is consistently off by more than +/- 5 um., then the [Beam Tilt calibrations](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Autofocus_Calibration_with_Beam_Tilt_Node) (defocus) may need to be repeated.

Make sure that the stage is at eucentric height in the calibration and that the [microscope has been well aligned](/leginon/Microscope_Set-up).

4. Clicking the Stop button ![](images/stop.png) exits the maunal check.

5. Leginon/Z Focus/Focus Sequence> Disable "Manual_after" focus step when it is not required.

## Select Exposure and Focus targets on the first image of a hole

Pick exposure and focus targets on the first image of a hole.

1. Leginon/Exposure Targeting> Click the Original, acquisition, and focus selections in the image control panel.

2. Check whether exposure (green crosshair) and focus (blue crosshair) targets were selected correctly.

3. Edit the targets by mouse left click (add) or right click (delete) on the target in the image viewer with the picking tool for the target type active.

4. If the exposure and focus selection is acceptable, uncheck "Allow for user verification of picked holes" in Leginon/Exposure Targeting/Settings>.

5. If the exposure and focus selection is not acceptable, try adjusting the Hole Finder to pick the correct targets. Refer to [Exposure Targeting Set-up](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Exposure-Targeting-Set-up).

6. Click "Submit Targets"

## Manually check focuser that uses Defocus as the correction method

Manually check the focus after the first high magnification images that are acquired. Then turn off "manual_after" focus step once it has been verified that the autofocus routine is properly correcting the defocus and astigmatism.


Manual Focusing can be activated either by enabling "Manual_before/Manual_after" steps or directly when leginon is idle using (Z) Focus/Toolbar/MF.

- Manual_before/Manual_after focus sequence:
- The preset used is set inside focus sequence settings ![](images/focus_sequence.png)
- Manual Focus Tool ![](images/manualfocus.png)
- When using Manual Focus Tool directly, the preset is set by the preset named "manual focus tool preset" found also in focuser node settings.

* MF> The FFT should show visible and isotropic Thon ring according to the fc preset defocus.

* MF/Toolbar> Make sure the move type is "Defocus" and the set value in the box is 0 m then click "Set instrument" botton ![](images/instrumentset.png). This will set the defocus to the current 0.

* MF> The perfect autofocus result is that the FFT indicates that the scope is at Gaussian focus.

* For relative movement, press "+" or "-". The step size is determined in MF/Toolbar/Settings> You can also left-click on the first node of the power spectrum displayed to change the step size.

* To reset defocus to zero at the new focus, press the so-named button ![](images/instrumentsetnew.png).

* Clicking the Stop button ![](images/stop.png) exits the manual check.


-   If the rings, after the direct setting to zero defocus in step 1, are still visable or are astigmatic in the FFT, then the [Beam Tilt calibrations](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Autofocus_Calibration_with_Beam_Tilt_Node) (defocus and stimator) may need to be repeated*

Make sure that the stage is at eucentric height and that the [microscope has been well aligned](/leginon/Microscope_Set-up).

4. Leginon/Focus/Focus Sequence> Disable "Manual_after" focus step when it is not required.

## View the images online

The images Leginon has acquired and published to the database can be viewed through the online viewers, the Leginon Image Viewer, the Leginon 3-Way Viewer, and the Leginon Observer Interface (LOI) which displays the currently acquired images.

1. Go to http://yourhost/myamiweb and open either the Leginon Image Viewer, the Leginon 3-Way Viewer, or the LOI.

2. Select today's Session from the pull-down list.

3. Have fun browsing through your images! You can view the parent images of images selected in the main viewer of the 3-way viewer in the smaller views by specify the appropriate preset.

## Interruption

Targets that are submitted can no longer be modified individually from the node where you selected them. If you need to abort the unprocessed targets in a list, you need to go to the node that receive it and click on the "Abort" button. In other words, if you want to abort all remaining holes in a square, you need to abort at the "Hole" node.

The same is true with pausing. Pausing is usually used when the cryo stage requires refill. To allow proper tracking of targets and drift, we recommend that you pause at "Hole" node for the purpose if exposure targets are not queued.

More information about interrupting data collection can be found in the [Trouble Shooting Chapter regarding pausing and aborting during data collection](/leginon/Leginon_Manual/Trouble_shooting/Pausing_and_Aborting_during_data_collection)

[< Special Operation setup](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Special_Operation_setup) | [Optimizing autofocusing >](/leginon/Optimize_Autofocusing)
