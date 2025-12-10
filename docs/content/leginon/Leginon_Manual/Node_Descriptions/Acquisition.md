The Acquisition node is the base node to acquire images with in a Leginon application. This node receives a Published Target List and navigates to each target using the specified Move Type. Then, an image is acquired and published to the database. Acquisition and Click Target Finders go together. The Click Target Finder nodes generate the list of targets and the Acquisition acquires images at each target. More than one preset can be assigned as a sequence to a single acquisition node; therefore, multiple images can be taken at each target. The ability to acquire many images at one target is how a defocal high magnification pair of images can be taken in the MSI application.

**Required bindings:**

AcquisitionNodeAlias- (ChangePresetEvent) -> PresetsManagerNode
PresetsManagerNode - (PresetChangedEvent) -> AcquisitionNodeAlias

**Bindings with the previous target makers or click target finder and the next click target finder:**

TargetMakerNodeAlias - (ImageTargetListPublishEvent) -> AcquisitionNodeAlias
AcquisitionNodeAlias - (TargetListDoneEvent) -> TargetMakerNodeAlias
AcquisitionNodeAlias - (AcquisitionImagePublishEvent) -> ClickTargetFinderNodeAlias
ClickTargetFinderNodeAlias - (ImageProcesstDoneEvent) -> AcquisitionNodeAlias

**Optional Bindings with DriftManager to allow target correction after drift:**

AcquisitionNodeAlias - (NeedTargetShiftEvent) -> DriftManagerNodeAlias
DriftManagerNodeAlias - (AcquisitionImageDriftPublishEvent) -> AcquisitionNodeAlias

**Optional Bindings with Navigator to allow (iterative) target move correction:**

AcquisitionNodeAlias - (MoveToTargetEvent) -> NavigatorNodeAlias

## Acquisition Toolbar ( Leginon/Acquisition/Toolbar> )

-   Settings = open the Acquisition Settings window to control behavior properties of the acquisition node


-   Play | Pause | Abort = controls how the acquisition node controls the target list. The abort button aborts only the current target list.


-   Queue Abort = Abort the whole target queue list.


-   Simulate Target = acquire an image with the current microscope settings and treat it as if it was passed to this acquisition node from another node. This avoids going through the process of a whole Leginon application in order to acquire an image with this node.


-   Simulate Target LoopPlay | LoopAbort = Acquire/Stop multiple simulated target acquisition that are separated by the time interval specified in the setting.


-   Browse Image= Load an image and publish it from this node and pass on to further processing (mainly for testing).

## Acquisition Settings ( Leginon/Acquisition/Settings> )

-   Use "image shift | stage position | modeled stage position | image beam shift" to move to target.
     
    The type of calibration movement that is used to navigate to the target. The target's previous preset's calibration is the one used, not the one that is assigned to the preset that the acquisition node will acquire the image at.
     
-   Wait "2.5" seconds before acquiring image.
     
    The amount of time paused before an image is acquired at the target after the target has been moved to.


-   Save image to database (on by default)
     
    Enabled means the image acquired with this node will be saved into the database. If this feature is disabled, the images will NOT be saved.


-   Wait for a node to process the image (off by default)
     
    Enabled means that the next image in the target list will not be acquired until all other nodes are finished processing the current image that was acquired with this acquisition node.
     
    The general rule for this settings is that, wait if there is a danger of competition for microscope. Therefore, do not wait at the final acquisition node in the acquisition sequence, nor when the image is fed to make an atlas that does not start further acquisition. If the next target finder node uses queuing option, there is no need to wait, either.


-   Publish and wait for rejected targets = If targets have been assigned to the target list that have not been assigned to this acquisition, enabling this option will make the acquisition node wait until those foreign targets have been processed/completed first. Acquisition nodes can only process acquisition targets. Ignoring the rejected targets would be the default unchecked position. This could also be a short-cut to turn off focusing (turn off this feature in the "exp" acquisition node in the MSI application. (off by default)


-   Adjust Target for Shift = This option is used with the binding of the acquisition node to DriftManagerNode to correct targets used to acquire the image. The target comes from a parent image. When it is on and if the target is expired by a drift after acquisition of the parent image, leginon reacquire an image using the parent image configuration and determine the correct by correlation with the original. Once
    corrected, other targets from the same parent image requires no further correction See [DriftManager](/leginon/Leginon_Manual/Node_Descriptions/Drift_Manager) Node Description (off by default)


-   Simulated Target Loop: Wait Time | Iterations= This is used with Simulate Target Loop tool. The wait time is between the end of the last acquisition and the beginning of the new acquisition.


-   Preset Order = the selected presets that appear in the white list box area are the presets used by the acquisition node to acquire images per target in the image target list.


-   Insert | Delete | Up | Down = adjust the presets assigned to this acquisition node


-   Mover: preset manager | navigator

In order to move to the target, Acquisition node uses either PresetsManager or Navigator. Moving handled by PresetsManager is the original design of Leginon which uses the calibration of the parent image where the target comes from to perform a single move, and it works for all move types. Moving handled by Navigator is a new feature available starting v1.3. Apart from single move, identical to that of PresetsManager, it
can perform iterative move correction that checks move error by locally correlating to the original image around the target and only stops trying when the error is below a threshold. As of v1.3, this function does not work with image shift move type.

-   Move Accuracy (m): The threshold for iterative movement by navigator. Entering 0 will result in a single move without error check.

[BeamFixer >](/leginon/Leginon_Manual/Node_Descriptions/BeamFixer)
