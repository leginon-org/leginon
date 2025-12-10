Queuing in "Hole Targeting" is useful when rare objects can be identified at "sq" preset and a quick survey of the grid is desirable before acquiring images at higher mags. An example for such a situation is for data acquisition of 2D crystals.

## Configuration

1. /Square/Toolbar/Setup/Wait for a node to process image = yes or no

**yes**: Pro-won't cause problem if you forget to change this when you decide not to use queuing later. Con-time wasted while holefinder is picking targets.

**no**: Pro-saves some time by acquiring images while holefinder and YOU are picking targets. Con-if you forget to switch it back on when you decide not to use queue later, many things can go wrong, starting from nodes competing for the microscope

2. /Hole Targeting/Toolbar/Setup/Queue up targets=yes.

"Declare drift when queue is submitted" is not necessary because Z focus, which is the first targets for each square parent image will cause a drift declare of its own.

3. /Hole/Toolbar/Setup/Wait for a node to process image = yes (as in MSI depth-first mode).

4. /Exposure Targeting/Toolbar/Setup/Queue up targets=no (as in MSI depth-first mode).

## Operation

1. Select square targets on grid atlas and submit as usual.

2. All sq images will be acquired while "Hole Targeting" finds the targets on each sq image if waiting in "Square" node is off. Note that since the square node acquires images continuously, both hole finding and acquisition may compete for processing and memory time. If it affects your interaction with the program, just wait for the acquisition to complete.

3. If you have just acquired many (such as 50) sq images in LM mode, the microscope has stayed in LM for a long time. It is advisable to set the instrument to one of the preset in HM mode as soon as the acquisitions are completed and check for possible image shift inconsistency between presets.

4. If user verification is turned on in "Hole Targeting", the targets should be submitted using "submit" ![](images/play.png) tool.

5. The Queue is submitted and processed only when "Submit Queued Target" ![](images/send_queue_out.png) tool is clicked.

6. Since queuing is not turned on at "Hole" and "Exposure Targeting" in this case, the data acquisition is ordered as in depth-first mode so that the exposure/focus targets on a hole are acquired before the next hole.

7. In case when leginon crashes during queue processing, the data acquisition should be resumed by "Submit Queued Target" ![](images/send_queue_out.png) in "Hole Targeting" node.

## Interruption

Once the queue is submitted there are several modes of interruption:

1. If leginon crashes during queue processing, the data queue acquisition can be resumed by "Submit Queued Target" in "Hole Targeting" node.

2. Exposure targets are paused and aborted as usual.

3. Queued targets can be paused in "Hole" node with "pause" button and is [recommanded for the liquid nitrogen refill of the side-entry cryo stage](/leginon/Leginon_Manual/Trouble_shooting/Pausing_and_Aborting_during_data_collection).

4. The "Abort" button ![](images/stop.png) in "Hole" node aborts the acquisition of the remaining targets from the same parent "hl" image and proceeds to process targets from next square in the queue.

5. The "Abort Queue" button ![](images/stop_queue.png) in "Hole" node aborts all remaining targets in the queue.

6. If you want to pause queue processing and switch to depth-first mode temporarily, and then continue the queue processing, do the following:

* "Pause" ![](images/pause.png) the queue in "Hole" node or "Exposure" node.

* Quit leginon once the program is standby in the paused mode.

* Restart leginon and the application.

* Change configuration to that of non-queuing mode and operate as such.

* When ready to continue queue processing, configure the related nodes as such when leginon is idle.

* Click on "Submit Queued Target" ![](images/send_queue_out.png) icon in "Hole Targeting".

7. Since Z focus is performed as the first target in the queue from individual square and there is no more z reverting for other holes in the square, you can rescue bad U-centric height adjustment during "Hole" and "Exposure" acquisition as in the full depth-first mode.

[< Queuing Example 1 - Exposure Targeting](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Queuing_Example_1_-_Exposure_Targeting) | [Queuing Example 3 - Both Exposure and Hole Targeting >](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Queuing_Example_3_-_Both_Exposure_and_Hole_Targeting)
