MSI-Tomography application is an example of such queuing set up. It is also the useful
when energy filter is used. It is chosen so that the microscope stays at the same presets as
long as possible to obtain all the images so that LM preset sq will not need to be used once
tomography data collection starts.

## Configuration

1. /Square/Toolbar/Setup/Wait for a node to process image = no

The "no" setting saves time by acquiring images while holefinder and YOU are picking targets.

2. /Hole Targeting/Toolbar/Setup/Queue up targets = yes.

3. /Hole Targeting/Toolbar/Setup/Allow user verification of the selected targets=yes, if desired.

4. /Hole/Toolbar/Setup/Wait for a node to process image = no.

5. /Exposure Targeting/Toolbar/Setup/Queue up targets = yes.

6. /Exposure Targeting/Toolbar/Setup/Allow user verification of the selected targets = yes, if desired.

## Operation

1. Select square targets on grid atlas and submit as usual.

2. All sq images will be acquired while "Hole Targeting" finds the targets on each sq
image since waiting in "Square" node is off. Note that since the square node acquires
images continuously, both hole finding and acquisition may compete for processing and
memory time. If it affects your interaction with the program, just wait for the
acquisition to complete.

3. If you have just acquired many (such as 50) sq images in LM mode, the microscope
has stayed in LM for a long time. It is advisable to set the instrument to one of the
preset in HM mode as soon as the acquisitions are completed and check for possible image
shift inconsistency between presets. If energy filter need to be on for higher
magnification imaging, do so now.

4. If user verification is turned on in "Hole Targeting", the targets should be
submitted using "submit" ![](images/play.png) tool.

5. The Queue is submitted and processed only when "Submit Queued Target" ![](images/send_queue_out.png) tool is clicked.

6. Repeat the same target selection and submission process at "Exposure Targeting" node.

7. In case when leginon crashes during queue processing, the data acquisition should be resumed by
"Submit Queued Target" ![](images/send_queue_out.png) in "Exposure Targeting" node first. If nothing happens, it means the queue in that node is empty. In that case, repeat it in "Hole Targeting" to resume.

## Interruption

Once the queue is submitted there are several modes of interruption:

1. If leginon crashes during queue processing, the data queue acquisition can be
resumed by "Submit Queued Target" in first the "Exposure Targeting Q" node, then if
nothing happens, in the "Hole Targeting" node.

2. Queued targets from "Hole Targeting" can be paused in "Hole" node with "pause"
button and is [recommanded for the liquid nitrogen refill of the side-entry cryo stage](/leginon/Leginon_Manual/Trouble_shooting/Pausing_and_Aborting_during_data_collection).

3. The "Abort" button ![](images/stop.png)
in "Hole" node aborts the acquisition of the remaining targets from the same parent "hl"
image and proceeds to process targets from next square in the queue.

4. The "Abort Queue" button ![](images/stop_queue.png) in "Hole" node aborts all remaining targets in the queue.

5. Exposure targets are paused and aborted in a way similar to the queued Hole Targets.

[< Queuing Example 2 - Hole Targeting only](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Queuing_Example_2_-_Hole_Targeting_only) | [Monitor Progress of Queued Targets >](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Monitor_Progress_of_Queued_Targets)
