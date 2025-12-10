Users may need to pause leginon data collection when filling cryo-stage and cold trap or making adjustment to image or beam shift of a preset or even perform certain microscopy alignment. Pausing is possible when leginon is waiting for user input at target finder level. Alternatively, pausing can be made in any acquisition node with the pause tool.

## For those using MSI-type of application, we recommand the following pausing point:

Case 1: Exposure Targets are NOT queued

-   At Hole or Subsquare (MSI-Raster) node, click on the "Pause" tool any time and it will pause before the start of next hole in the same square.

Case 2: Exposure Targets are queued

-   In Focus node and click on the "Pause" tool while the Exposure target is being acquired. Leginon will then pause at the end of the exposure sequence before the next Focus target is processed.

The pause tool (as well as the abort tool), when clicked, does not interrupt acquisition until the next possible point that is at the end of an acquisition sequence for a target. When the play tool is clicked at a later point of time, leginon should move the stage and image shift to that defined by the next image. Here are some examples of the valid pausing
points.

-   At the end of an acquisition sequence for a target in the middle of a target list that may also be one of the queued list.
-   At the end of an acquisition sequence for a target at the end of a target list that may also be one of the queued list.
-   Before a focus target is repeated after DriftManager is done monitoring drift.

Currently, you can not pause at the following points:

-   Within the preset list of an acquisition target.
-   Before any target is processed at the node.

[< Do and Do Not in leginon](/leginon/Leginon_Manual/Trouble_shooting/Do_and_Do_Not_in_leginon) | [Aborting targets that are not yet being processed >](/leginon/Leginon_Manual/Trouble_shooting/Aborting_targets_that_are_not_yet_being_processed)
