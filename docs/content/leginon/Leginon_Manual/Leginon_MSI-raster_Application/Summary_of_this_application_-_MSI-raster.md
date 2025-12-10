The Leginon "MSI-raster" application is essentially a duplicate of "MSI-Edge" or "MSI-T" except that the Hold Finder nodes have been replaced by Raster Finder nodes. The raster finder nodes can pick raster targets across an image in order to image negatively stained grids for example. MSI raster is a 5-stage acquisition process which includes a grid atlas, squares acquisition, holes acquisition, focusing, and final exposures. Target finding at each stage leads to acquisition at the next stage. Drift management and autofocusing is also involved. The following list is a cursory glance at the steps to run this application:

* Calibrations (autofocus, image shift, stage position, modeled stage position, ...)

* Set-up Presets (gr, sq, hl, fa, fc, en, ef)

* Acquire Corrector images.

* Configure the node preferences (all raster finder nodes, all acquisition nodes, focuser node).

* Acquire a grid atlas.

* Select squares on the grid atlas. The process is wholly automated from this point until more squares are selected.

* Optionally interact with the raster finders.

Since MSI raster is essentially the same as other MSI, reference "MSI in general" chapter for help on the entire process of setting up and operating MSI raster. The main difference is how to set-up the raster finder nodes.

[Pre-MSI Set-up](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Pre-MSI_Set-up): Prior to setting up Leginon for the day, make sure that Leginon has been previously set-up (this step is in case the ambitious user decides to proceed to this section for the first time and hasn't gone through all the calibrations...).

[MSI preference and configuration](/leginon/Leginon_Manual/Preferences_Setup/Initial_MSI_application_preference_setup): The comprehensive MSI preferences and configuration example. The node name change in MSI raster are: "Hole Targeting" -> "Sub-Square Targeting" and "Hole" -> "Sub-Square".

[MSI Quick Start checklist](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_Quick-start): A short check list for users who are familiar with the application and have saved preferences.

[MSI set-up in more details](/leginon/MSI_set-up_in_more_details): The more complicated MSI Leginon application set-up that should be completed before collecting data.

[Queuing option](/leginon/MSI_set-up_in_more_details): An option that groups human interaction together by putting the submitted targets from different images at the same level of target finders into a queue and process them later.

[Trouble shooting](/leginon/Leginon_Manual/Trouble_shooting): This trouble shooting sections addresses some of the possible challenges a Leginon user may face.

In this chapter:

[Raster Finder nodes set-up](/leginon/Leginon_Manual/Leginon_MSI-raster_Application/Raster_finder_nodes_set-up): A short guide to set-up the raster finder nodes in the MSI raster Leginon application.

NOTE: The Tietz imaging software (EMMenu) must be turned OFF before Leginon is started. In contrast to this, the Gatan imaging software (Digital Micrograph) must be ON before Leginon is started.

[raster finder nodes set-up >](/leginon/Leginon_Manual/Leginon_MSI-raster_Application/Raster_finder_nodes_set-up)
