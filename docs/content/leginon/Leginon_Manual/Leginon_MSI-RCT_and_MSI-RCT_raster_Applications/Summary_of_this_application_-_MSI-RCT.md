Random conical tilt (RCT) and orthogonal tilt reconstruction (OTR) image acquisition schemes require images pairs taken at two different tilt angles. The two Leginon "MSI-RCT" applications replace the Exposure node with a specialized node that acquire a batch of targets at one tilt and then the other. A feature matching algorithm is used to transform targets from the selected targets on one parent image at one tilt to the other tilt (and more tilts if needed).

The two applications differ in the target finding nodes. Therefore, MSI-RCT is suitable for specimen suspended in regular holes from support film such as Quantifoil and C-flat. MSI-RCT-raster is suitable for specimen lay down on continuous carbon film

See [JAHC finder nodes set-up](/leginon/JAHC_finder_nodes_set-up) and [Raster finder nodes set-up](/leginon/Leginon_Manual/Leginon_MSI-raster_Application/Raster_finder_nodes_set-up) on how to setup automated targetfinders in the two cases.

Reference "MSI in general" chapter for help on the entire process of setting up . The main difference is that the preset used to acquire the parent image of RCT targeting is set at a magnification in the HM mode to give large viewing area and offer the stronger feature contrast needed for the target transformation between tilts.

## [Ideal grids for automated RCT acquisition](/leginon/Leginon_Manual/Leginon_MSI-RCT_and_MSI-RCT_raster_Applications/Best_grids_for_RCT): grids with distinct feature at more than one scale level.

## [Example of high-mag images with good negatively stain esential for RCT acquisition](/leginon/Leginon_Manual/Leginon_MSI-RCT_and_MSI-RCT_raster_Applications/Summary_of_this_application_-_MSI-RCT/Good_negative_stained_images_for_RCT)

## [RCT nodes set-up](/leginon/Leginon_Manual/Leginon_MSI-RCT_and_MSI-RCT_raster_Applications/RCT_node_set-up): A short guide to set-up the RCT node in these applications.

## Further reading

[Pre-MSI Set-up](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Pre-MSI_Set-up): Prior to setting up Leginon for the day, make sure that Leginon has been previously set-up (this step is in case the ambitious user decides to proceed to this section for the first time and hasn't gone through all the calibrations...).

[MSI preference & configuration](/leginon/Leginon_Manual/Preferences_Setup/Initial_MSI_application_preference_setup): The comprehensive MSI preferences and configuration example. The node name change in MSI raster are: "Hole Targeting" -> "Square Centering", "Hole" -> "Centered Square", "Exposure Targeting" -> "RCT Targeting", "Focus" ~~["RCT Focus", and "Exposure"]{style="text-align:right;"}~~>"RCT".

[MSI Quick Start checklist](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_Quick-start): A short check list for users who are familiar with the application and have saved preferences.

[MSI set-up in more details](/leginon/MSI_set-up_in_more_details): The more complicated MSI Leginon application set-up that should be completed before collecting data.

[Queuing option](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Queuing_option): "RCT Targeting" node is operated in queuing mode.

[Iterative Stage Movement](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Iterative_Stage_Movement): "RCT" node target centering uses this option.

[Trouble shooting](/leginon/Leginon_Manual/Trouble_shooting): This trouble shooting sections addresses some of the possible challenges a Leginon user may face.

## [RCT run protocol from a user](/leginon/Leginon_Manual/Leginon_MSI-RCT_and_MSI-RCT_raster_Applications/RCT_run_protocol_from_a_user)

[RCT node set-up >](/leginon/Leginon_Manual/Leginon_MSI-RCT_and_MSI-RCT_raster_Applications/RCT_node_set-up)
