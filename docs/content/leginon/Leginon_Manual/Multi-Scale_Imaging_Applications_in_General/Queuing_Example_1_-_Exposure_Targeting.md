Queuing targets for Exposure node is used when a large number of exposure images need to be acquired and immediate need of evaluation is required only up to intermediate mag of Hole images. One example for such data collection mode is during high throughput single particle data acquisition.

## Configuration

Use the configuration for MSI until queuing is about to be used.

1. /Square/Toolbar/Setup/Wait for a node to process image = yes (as in depth-first MSI).

2. /Hole Targeting/Toolbar/Setup/Queue up targets=no (as in depth-first MSI).

3. /Hole/Toolbar/Setup/Wait for a node to process image = yes or no

**yes**: Pro-It won't cause problem if you forget to change this when you decide not to use queuing later. Con-Time is wasted while holefinder picks targets. (recommended)

**no**: Pro-It saves some time by acquiring images while holefinder and YOU are picking targets. Con-If you forget to switch it back on when you decide not to use queue later, many things can go wrong, starting from nodes competing for the microscope

4. /Exposure Targeting/Toolbar/Setup/Queue up targets=yes.

"Declare drift when queue is submitted" is optional but recommended. Use it if accurate targeting is required. The time required to finish target will be longer.

5. /Exposure Targeting/Toolbar/Setup/Declare drift when queue is submitted=yes.

You may leave it off if you do not require acturate targeting (>0.5 um). The time
required to finish target will be longer with the option on.

6. /Z Focus/Focus Sequence/Manual_after Enable=yes (optional but highly recommended because further z height adjustment in Focus node affects only the current hole in queuing mode)

## Operation

1. Select square targets on grid atlas and submit as usual.

2. One sq image will be acquired and then "Hole Targeting" finds the targets on the sq image.

3. If user verification is turned on in "Hole Targeting", the targets should be submitted using "submit" ![](images/play.png) tool.

4. The Z focus target will be processed first and the grid U-centered at the square.

5. [Check if the grid is at U-center height in manual focus window](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_Operation#Manually-check-focuser-that-uses-Stage-Z-as-the-correction-method). Note that you won't see nice Thon rings because the preset is "hl"

6. All hl images from the sq images will be acquired while "Exposure Targeting" finds the targets on each hl image if waiting in "Hole" node is off. Note that since the "Hole" node acquires images continuously, both hole finding and acquisition may compete for processing and memory time. If it affects your interaction with the program, just wait for the acquisition to complete.

7. If user verification is turned on in "Exposure Targeting", the targets should be submitted using "submit" ![](images/play.png) tool.

8. You may refresh atlas in "Square Targeting" and repeat the above steps to add more targets to the queue.

9. The Queue is processed only when "Submit Queued Target" ![](images/send_queue_out.png) icon is clicked.

**Important: You should only do Submit Queued Target when leginon IS DONE acquiring image if there is no waiting on "Hole". Otherwise, the "Hole" and "Exposure" nodes may compete for the microscope and you can have images with the wrong magnification.

## Interruption

Hole and Square acquisitions are paused and aborted as usual.

Once the queue is submitted there are several modes of interruption:

1. If leginon crashes during queue processing, the data queue acquisition can be resumed by "Submit Queued Target" ![](images/send_queue_out.png) in "Exposure Targeting" node.

2. Queued targets can be paused in "Exposure" node with the "pause" button and is [the recommanded pausing point for the liquid nitrogen refill of the side-entry cryo stage](/leginon/Leginon_Manual/Trouble_shooting/Pausing_and_Aborting_during_data_collection).

3. The "Abort" button ![](images/stop.png) in "Exposure" node aborts the acquisition of the remaining targets from the same parent "hl" image and proceeds to process targets from next hole in the queue.

4. The "Abort Queue" button ![](images/stop_queue.png) in "Exposure" node aborts all remaining targets in the queue.

5. If you want to pause queue processing and switch to depth-first mode temporarily, and then continue the queue processing, do the following:

* "Pause" the queue in "Exposure" node.

* Quit leginon once the program is standby in the paused mode.

* Restart leginon and the application.

* Change configuration to that of non-queuing mode and operate as such.

* When ready to continue queue processing, configure the related nodes as such when leginon is idle.

* Click on "Submit Queued Target" ![](images/send_queue_out.png) icon in "Exposure Targeting".

6. Since the queued targets first reverts to its parent image stage position (including stage Z), you CAN NOT rescue bad U-centric height adjustment once the queue is submitted. You will have to abort the targets from the same square and hope the next square works.

7. You can still change image shift, beam shift, exposure time of the presets during queue processing. Again, pause the queue and first send the problem preset to scope before making adjustment. You are warmed that the current location will be sacrificed during this process if the sample is exposed to the beam during your adjustment.

## Adding more targets to the queue

It is possible to add more targets to the queue even when the queue is still being processed. The reason is that "Submit Queued Target" ![](images/send_queue_out.png) really only signals that there are new targets updated to the queue that is to be processed.

1. Pause in "Exposure" node with the "pause" ![](images/pause.png) button and is [the recommended pausing point for the liquid nitrogen refill of the side-entry cryo stage](/leginon/Leginon_Manual/Trouble_shooting/Pausing_and_Aborting_during_data_collection#Pausing-in-MSI-application).

2. Go to "Square Targeting" node, submit more square targets.

3. Go to "Hole Targeting" node, submit more hole and z-focus targets as the images come in.

4. Go to "Exposure Targeting", submit ![](images/play.png) to the queue more exposure and focus targets as the images

5. When you have enough targets, click on "Submit Queued Target" ![](images/send_queue_out.png) icon in "Exposure Targeting".

6. Go back to "Exposure", click on ![](images/play.png)to continue data acquisition.

[< Queuing option](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Queuing_option) | [Queuing Example 2 - Hole Targeting only >](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Queuing_Example_2_-_Hole_Targeting_only)
