## Introduction

Queuing option puts in a queue the selected targets on multiple images from the same acquisition node. The queue can then processed as a batch. Therefore, targets from multiple squares can be selected before any hole image image is acquired in any grid square. Alternatively, targets from multiple holes of the same square can be selected before any exposure is taken. Because the event bindings are identical in MSI application. Target processing scheme can be switched between the queuing (breadth-first) mode and the depth-first mode at appropriate point.

![](images/MSIQtree.png)

In queuing mode, the movement of the stage is more complicated as targets in the same subtree are not acquired in close time frame and often need readjustment of targets when it is finally the time to acquire the child image. This is all taken care of by the drift manager by reversing the stage position (including stage z) of the parent image when the first child image is to be acquired after the drift declared event. Users of the queuing mode should know that this frequent interaction with the drift manager makes the time for completing the target list longer but is necessary when targeting accuracy is important.

The other consideration is that if queuing is activated at Hole Targeting node so that a large number of images are acquired in "sq" preset at LM mode in a batch without ever cycling to HM presets, the objective lens may cool down sufficiently that the image alignment is different from during normal acquisition cycle. We recommend that either setting the scope to one of the HM mode, wait for 30 or more minute and recheck the image alignment or processing a smaller batch of "sq" preset each time so that the scope does not operate in LM for extended amount of time. Our experience is that it is better not to activate queuing at Hole Targeting but queue up only at exposure targeting so that the above problem is less likely to occur.

[Trouble shooting](/leginon/Leginon_Manual/Trouble_shooting)

## Initial Queuing set-up

The user should start with [the preference and configuration](/leginon/Leginon_Manual/Preferences_Setup/Initial_MSI_application_preference_setup) of the nodes in MSI application in the depth-first mode and follow the [quick start procedure](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_Quick-start). Once the function of all nodes are confirmed to be normal, then switch to queuing. There are two possible points for queuing, at Hole Targeting or at Exposure Targeting. The two can be used in any combination with the depth-first mode.

## We highly recommend that you activate "Use ancestor image mover in adjustment" the acquisition node whose parent moves to targets by iterative Navigator stage movement if you want to use image shift to do final targeting. It will reduce the amount of image shift applied if you have concern for excessive image shift.

Example:

-   Activate "Use ancestor image mover in adjustment" in "Exposure" node if "Hole" is uses Navigator as (modeled) stage position mover, and "Navigation Tolerance" is larger than zero.

## Configuration and operation rules for a chosen queuing point

Configuration of two nodes are affected by each queuing and they should be set in the following order if the two are currently processing data:

1. The option for "Queue up targets" should be selected in the HoleFinder. "Declare drift when queue is submitted" is optional. Use it if accurate targeting is required. The time required to finish target will be longer.

2. The acquisition node that acquires the image on which targets will be selected do not need to wait for HoleFinder node to process the image before next acquisition. This option is deselected in /Tool/Setup/. Leave it on if you are willing to wait for HoleFinder before next image acquisition.

In operation, the behavior of the above two nodes plus the acquisition node after the queuing holefinder are affected.

1. All targets submitted to the above-mentioned acquisition node will be acquired first(Waiting off) rather than one after each target submission (Waiting on). These targets would be considered "done" by Leginon at restart or target refresh.

2. The normal "submit" ![](images/play.png) in the targetfinder only stores the selected targets in the queue rather than proceeding to target processing.

3. Upon "Submit Queue" ![](images/send_queue_out.png) the queued target list is processed by the next acquisition node in which individual targets can be aborted by the abort button ![](images/stop.png), paused as in MSI, and the whole queue list can be aborted using the abort queue button ![](images/stop_queue.png).

4. The queued target list is in fact a list of lists where targets are grouped by their parent images. At the start of target processing of any unfinished sub-list by an acquisition node, leginon reverts the z stage position to that of the parent and processes rejected targets (i.e., the focus targets) first if the option is on as it is for "Hole" and "Exposure" nodes whether they have been processed previously. The rest of the unfinished acquisition targets are then processed.

5. The targets that generate images in the non-waiting acquisition node is considered done once acquired. Therefore, if Leginon is interrupted and restarted, you can not continue the acquisition and process the queued targets by submiting refreshed targets in "Square Targeting" node as in MSI. Instead, you should resubmit the queue in the corresponding holefinder node. Leginon will find out which targets have not been completed and continue the acquisition.

[< Adding a new focus sequence to a focus node](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Adding_a_new_focus_sequence_to_a_focus_node) | [Queuing Example 1 - Exposure Targeting >](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Queuing_Example_1_-_Exposure_Targeting)
