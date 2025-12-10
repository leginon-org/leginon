RCT stands for Random Conical Tilt. It can also used for Orthogonal Tilt image acquisition. This should be used with Navigator multiple move for best results.

**Required bindings to Presets Manager:**

RCTNode - (ChangePresetEvent) -> PresetsManagerNode
PresetManagerNode - (PresetChangedEvent) -> RCTNode

**Required bindings to a Target Finder:**

TargetFinderNode - (ImageTargetListPublishEvent) -> RCTNode
RCTNode - (TargetListDoneEvent) -> TargetFinderNode

**Required Bindings with Navigator to allow (iterative) target move correction:**

RCTNode - (MoveToTargetEvent) -> NavigatorNodeAlias

**Required Bindings for waiting for drift to stop after tilting:**

RCTrNode - (DriftMonitorRequestEvent) -> DriftManagerNode
DriftManagerNode - (DriftMonitorResultEvent) -> RCTNode

**Required Binding to correct drift from tilting as well as thermal expansion:**

RCTNode - (NeedTargetShiftEvent) - > DriftManagerNode
DriftManagerNode~~(AcquisitionImageDriftPublishEvent)~~> RCTNode

**Required Bindings to use drift check image in the node (???):**

DriftManagerNode - (AcquisitionImagePublishEvent) -> RCTNode

*see also [RCT run protocol from a user](/leginon/Leginon_Manual/Leginon_MSI-RCT_and_MSI-RCT_raster_Applications/RCT_run_protocol_from_a_user)*

[< Raster Filter](/leginon/Leginon_Manual/Node_Descriptions/Raster_Filter) | [Robot >](/leginon/Leginon_Manual/Node_Descriptions/Robot)
