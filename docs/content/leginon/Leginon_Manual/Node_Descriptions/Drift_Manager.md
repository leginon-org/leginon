The Drift Manager monitor has two functions. It works with [Transform Manager](/leginon/Leginon_Manual/Node_Descriptions/Transform_Manager_) to keep the accuracy of targeting through long experiment and certain operation such as the change of stage z position.

-   Monitoring drift when requested


-   Declaring that a drift has occured.

The first way of determining that drift is occurring is by measuring it directly. A drift measurement is initiated in one of two ways:

-   The user may manually monitor drift in the DriftManager node. This can be either a single measurement of the current drift rate or a loop that measures the drift rate until it falls below a threshold set in the DriftManager settings dialog.


-   The Focus node can request drift monitoring in preparation for doing auto focus. If drifting is in progress, DriftManager enters a measurement loop until drift falls below the threshold and declares that a drift has occured

Drifting can also be assumed to have occurred without doing a measurement. This is done as a result of certain operations of Leginon:

-   When stage Z position is changed, there is often a side effect of X and Y position shifting also. Drift is always declared after stage Z correction is made in a focus sequence.


-   When in queuing mode, it is often desirable to assume that drift has occured whenever a queue of targets is submitted. This is due to the possible long time durations and large stage movements. There is an option in each targeting node to "Declare drift when queue submitted".


-   Sometimes targeting accuracy is failing because the image from which the targets were selected was acquired using a preset with a bad image shift. The targets can be corrected using the following method: pause the processing of the targets, adjust the image shift of the bad preset, declare drift in DriftManager, continue processing the targets. The image shift adjustment will be treated as a drift and the targets will be corrected.


-   When various environmental factors have changed that the user thinks have caused a drift. One example is filling up the liquid nitrogen dewar. In this case, the user must click the "Declare Drift" button in the DriftManager node.

In the above cases, whether drift is measured or assumed, a drift time stamp is entered into the database to mark when the drift occured. Acquisition nodes have an option "Adjust targets for drift" which causes them to look for these drift time stamps before processing a target and acquiring an image. If a drift occured after the target was created, the target is declared invalid. To adjust the target, the Acquisition node must send a request to the DriftManager to measure the total drift that has occurred since the target was created. The
DriftManager will load the target's parent image from the database and reacquire it under its original imaging conditions as a different version. The correlation shift is then stored in the database so that any target that came from this image can be adjusted in the same way.

**Initiating drift monitoring by a focuser node requires two bindings to do such task:**

FocuserNode - (DriftMonitorRequestEvent) -> DriftManagerNode
DriftManagerNode - (DriftMonitorResultEvent) -> FocusNode

**For DriftManager to change presets, two bindings are needed:**

DriftManagerNode - (ChangePresetEvent) -> PresetsManagerNode
PresetsManagerNode ~~(PresetChangedEvent)~~> DriftManagerNode

## Settings

-   Wait for drift to be less than "3e-10" m = the distance threshold for drift checking to stop. A drift above the threshold will cause the Drift Manager to continue to monitor drift.


-   Wait "2.5" seconds between checking drift = the amount of time paused between acquisition of images to measure drift. This applies to requests from Focuser nodes, too.


-   the typical [Instrument and Camera Configuration](/leginon/Leginon_Manual/Node_Descriptions/Presets_Manager#Parameters-Instruments)

## Toolbar

-   Measure Drift = stand alone button to quickly and manually assess drift once.


-   Check Drift = stand alone button to start drift monitoring sequence.


-   Abort = this will abort the Drift Manager drift monitoring sequence.

[< Dose Calibrator](/leginon/Leginon_Manual/Node_Descriptions/Dose_Calibrator) | [The EM node >](/leginon/Leginon_Manual/Node_Descriptions/The_EM_node)
