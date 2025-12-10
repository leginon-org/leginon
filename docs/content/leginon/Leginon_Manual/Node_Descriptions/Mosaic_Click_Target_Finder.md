Mosaic Click Target Finder is a type of TargetFinder Node. It handles the loading, save, displaying and target selection of a list of images and and their composite.

**Required bindings for Mosaic Click Target Finder Node:**

Grid Targeting - (ImageTargetListPublishEvent) - > AcquisitionNodeAlias
AcquisitionNodeAlias- (AcquisitionImagePublishEvent) -> MosaicClickTargetFinder
MosaicClickTargetFinder - (ImageTargetListPublishEvent) -> AcquisitionNodeAlias
ClickTargetFinder - (ReferenceTargetListPublishEvent) -> AlignZeroLossPeak or MeasureDose

**Required bindings for MosaicClickTargetFinder Node if Reference Targets are used:**

MosaicClickTargetFinder - (ReferenceTargetListPublishEvent) -> AlignZeroLossPeak or MeasureDose

## Toolbar

-   Tiles = Choose The Mosaic Tiles label (aka atlas label) to display. Mosaic Tiles are a list of images collected by an Acquisition node upstream.


-   Mosaic = Select how large the mosaic atlas image will be and what calibration is used to create it.


-   Refresh = Refresh the "Mosaic" selector to the current choices in the database.


-   Show Position = When clicked, the current microscope position (orange crosshair) will be updated on the atlas image.


-   Find Squares = An automatic algorithm for detecting squares on the atlas image.


-   Submit Targets = Submit the selected squares for processing.

## Tiles

-   Load tiles from mosaic = Choose The Mosaic Tiles label (aka atlas label) to display. Mosaic Tiles are a list of images collected by an Acquisition node upstream.


-   Reset = Clears the loaded list in the Mosaic Click Target Finder, and therefore clears the mosaic image shown.

## Mosaic Settings

-   Calibration parameter (stage position | image shift | modeled stage position) = Select the type of calibration used to create the atlas. Stage Position should be used. This determines how the node creates the pixel shifts for each tile image in order to "paste" it to the right position of the mosaic image. Each acquired image in the database has the full information on its stage position and image shift. This pull-down selector determines which items the subnode look into for the conversion into pixel shift.


-   Scale image to "1000" pixels in largest dimension = When enabled, the mosaic atlas will be scaled to this image size.


-   Mosaic Image (Create | Save) = Create and save the large mosaic atlas to the database.

## Image Control Panel

-   acquisition = Use this to select NEW targets shown in a greeen crosshair.


-   done = The done targets (squares already visited) will be shown with a red crosshair.


-   position = The current position of the microscope relative to the grid is shown with an orange crosshair.


-   image = The atlas image is shown.


-   Filtered = This is used for the automatic square selection algorithm


-   Thresholded = This is also used the the automatic square selection algorithm

[< Matrix Calibrator](/leginon/Leginon_Manual/Node_Descriptions/Matrix_Calibrator) | [Mosaic Target Maker >](/leginon/Mosaic_Target_Maker)
