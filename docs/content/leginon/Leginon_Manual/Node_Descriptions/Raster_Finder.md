A subclass of TargetFinder

**Required bindings for recieving images and publishing targets:**

previous Acquisition - (AcquisitionImagePublishEvent) -> Hole Finder
Hole Finder - (ImageTargetListPublishEvent) -> next Acquisition
Hole Finder - (QueuePublishEvent) -> next Acquisition

**Required bindings for proper waiting among nodes:**

Hole Finder- (ImageProcessDoneEvent) -> previous Acquisition
next Acquisition - (TargetListDoneEvent) -> Hole Finder

[< Presets Manager](/leginon/Leginon_Manual/Node_Descriptions/Presets_Manager) | [Raster Filter >](/leginon/Leginon_Manual/Node_Descriptions/Raster_Filter)
