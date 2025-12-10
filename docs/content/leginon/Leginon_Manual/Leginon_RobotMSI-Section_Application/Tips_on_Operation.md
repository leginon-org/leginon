## Presets

-   This application does not need sq, en, and ef preset.


-   Keep fa and fc preset if accurate defocus is necessary. The default values assume fa and fc do not exist.


-   You may also use lower magnification for gr preset to reduce the time required for acquire the grid atlas.


-   It is more efficient to use lower mag and lower camera binning on the "hl" preset used for final acquisition

## Warm up objective lens after acquiring grid atlas

-   With enough over raster overlap and large enough raster, there is no need to do this.

## Grid Targeting Robot Node

-   Enter a unique name for the grid as Mosaic Label so that you can collect images on multiple grids in the same session and have the label displayed on the web viewer.

## Move Type

-   Use modeled-stage position move type for all Acquisition and Focuser nodes because the movement is always large.

## Section Z Focus Node

-   The focus target is selected on the grid atlas in "Raster Center Targeting" node.


-   It may help to follow the [focus sequence suggested in MSI-Raster Application](/leginon/Leginon_Manual/Leginon_MSI-raster_Application/Improving_Autofocusing), but use "gr" preset for Stage_Wobble step. If this is difficult due to the inserted objective aperture, you will still need to use a "sq" preset that is about 500-800x.

## Pre-exposure

-   In certain cases, a pre-exposure is required for image stability. Adding "gr" preset to "Final Section" so the region is first exposed over a large area has been shown to help more than a local pre-exposure defined by "hl" preset.

## Queuing

-   "Raster Center Targeting" is always in queuing mode.

[< Other special preference set-up](/leginon/Leginon_Manual/Leginon_RobotMSI-Section_Application/Other_special_preference_set-up) | [Leginon "RobotMSI-Section" Application ^](/leginon/Leginon_Manual/Leginon_RobotMSI-Section_Application)
