The Transform Manager handles all shift corrections that need to be done after drift is declared. The class will be expand to do transformation other than shift in the future.

By the request of an Acquisition Node, the transform manager reaquires ancestors of the target that requires transformation in order to create the transformed target.

Any acquisition or focuser node that need target correction requires two bindings.

AcquisitionNode or FocuserNode - (TransformTargetEvent) - > TransformManagerNode
TransformManagerNode~~(TransformTargetDoneEvent)~~> AcquisitionNode orFocuserNode

For TransformManager to change presets, two bindings are needed:

TransformManagerNode - (ChangePresetEvent) -> PresetsManagerNode
PresetsManagerNode ~~(PresetChangedEvent)~~> TransformManagerNode

## Settings

-   Minimal Magnification = 300. This setting sets a lower limit to the ancestor image reacquisition. It can be set to prevent going down to a magnification where the objective aperture inserted after the original image was acquired prevents correlation between the reaquired image (with aperture) and the original (without aperture). Alternatively, it can be set to prevent the reacquisition that uses the LM mode.

## Toolbar

-   Declare Drift = force the Transform Manager to start drift correction sequence.

[< Tomography](/leginon/Leginon_Manual/Node_Descriptions/Tomography)
