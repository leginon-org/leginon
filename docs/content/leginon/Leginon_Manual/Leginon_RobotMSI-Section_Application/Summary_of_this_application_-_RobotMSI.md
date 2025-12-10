"RobotMSI-Section" application is a simplified MSI-Raster with interface to grid-loading robot. Without the robot and project database structure for grid management (not released), this application can still be used with manual grid loading and entry of grid name at appropriate place. A better application "MSI-Section3step" is also available and should be used instead if possible.

-   Calibrations (autofocus, image shift, stage position, modeled stage position, ...)


-   Set-up Presets (gr, hl)


-   Acquire Correction images.


-   Enter a unique label for the grid atlas at the Grid Targeting Robot node.


-   Acquire a grid atlas.


-   Select center of the section on the grid atlas.


-   If necessary, adjust raster parameter at the Raster Generation node.


-   Check raster overlap and image quality on the web viewers.

Reference "MSI in general" chapter for help on the entire process of setting up and operation. Reference The set up of the Raster Generation node (of RasterTargetFilter Class) is very similar to [Raster Finder nodes](/leginon/Leginon_Manual/Leginon_MSI-raster_Application/Raster_finder_nodes_set-up)

[Pre-MSI Set-up](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Pre-MSI_Set-up): Prior to setting up Leginon for the day, make sure that Leginon has been previously set-up (this step is in case the ambitious user decides to proceed to this section for the first time and hasn't gone through all the calibrations...).

[MSI preference and configuration](/leginon/Leginon_Manual/Preferences_Setup/Initial_MSI_application_preference_setup): The comprehensive MSI preferences and configuration example. The node name change in RobotMSI-Section are: "Grid Targeting" -> "Grid Targeting Robot" and "Hole" -> "Final Section". Nodes not found in this application are irrelevent for this application.

[MSI Quick Start checklist](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_Quick-start): A short check list for users who are familiar with MSI applications.

[MSI set-up in more details](/leginon/MSI_set-up_in_more_details): The more complicated MSI Leginon application set-up that should be completed before collecting data.

[Trouble shooting](/leginon/Leginon_Manual/Trouble_shooting): This trouble shooting sections addresses some of the possible challenges a Leginon user may face.

In this chapter:

NOTE: The Tietz imaging software (EMMenu) must be turned OFF before Leginon is started. In contrast to this, the Gatan imaging software (Digital Micrograph) must be ON before Leginon is started.

[^ Leginon "RobotMSI-Section" Application](/leginon/Leginon_Manual/Leginon_RobotMSI-Section_Application) | [Raster Generation node set-up >](/leginon/Leginon_Manual/Leginon_RobotMSI-Section_Application/Raster_Generation_node_set-up)
