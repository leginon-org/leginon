It is really a raster generator. It adopted the name because it is a subclass of
TargetFilter that takes in targets and output targets.

**Required bindings for recieving targets and publishing targets:**

previous Target Finder - (TargetListPublishEvent) -> Raster Filter
Target Filter - (ImageTargetListPublishEvent) -> next Acquisition
Target Filter - (QueuePublishEvent) -> next Acquisition

**Required bindings for proper waiting among nodes:**

Raster Filter- (TargetListDoneEvent) -> previous Target Finder
next Acquisition - (TargetListDoneEvent) -> Raster Filter

[< Raster Finder](/leginon/Leginon_Manual/Node_Descriptions/Raster_Finder) | [RCT >](/leginon/Leginon_Manual/Node_Descriptions/RCT)
