All the MSI applications share the same scheme. They are 5-stage acquisition processes
which include a grid atlas, squares acquisition, holes (called subsquare in MSI-Raster)
acquisition, focusing, and final exposures (Tomography for MSI-Tomography). Target finding at
each stage leads to acquisition at the next stage. Drift management, eucentric height
correction, and autofocusing is also involved. The diagram below shows the flow of control in
MSI. The detailed event bindings involved are for advanced users only and can be found in the
chapter covering creating/editing application at the end of the full manual.

![](images/MSI_flow.png)

The black arrows show the flow of execution from the node where the arrow starts
on initiation of execution to the node that the arrow is pointed to. The green arrow shows
the control of target shift correction by drift manager. The red,blue, purple, and magenta
frames enclose nodes that processes acquisition, focus, reference and preview targets,
respectively. These nodes set presets through Presets Manager and moved to their targets
using either Presets Manager or Navigation node. The green frames are nodes for drift
management.

The following list is a cursory glance at the steps to run this application:

-   Calibrations (autofocus, image shift, stage position, modeled stage position, ...)


-   Set-up Presets (gr, sq, hl, fa, fc, en, ef)


-   Acquire Corrector images.


-   Acquire a grid atlas.


-   Select squares on the grid atlas. The process can be wholly automated from this point until more squares are selected.


-   Optionally interact with the hole finders.


-   Optionally putting targets from different images at the same level into queue that
    can be processed in a batch.

This chapter has been divided into sections to facilitate everyday usage:

[Pre-MSI Set-up](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Pre-MSI_Set-up): Prior to setting up Leginon for the day, make sure that the presets have been designed and Leginon calibrated for your purpose.

[MSI preferences and configuration](/leginon/Leginon_Manual/Preferences_Setup/Initial_MSI_application_preference_setup): The comprehensive MSI preferences and configuration example.

[MSI Quick Start checklist](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_Quick-start): A short check list for users who are familiar with the application and have saved preferences.

[MSI set-up in more details](/leginon/MSI_set-up_in_more_details): The more complicated MSI Leginon application set-up that should be completed before collecting data.

[MSI queuing option](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Queuing_option): Introduction to the queuing option.

[MSI Exposure Target queuing](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Queuing_Example_1_-_Exposure_Targeting): The setup and operation of queuing mode for large number of exposure targets and/or for avoiding accessing sq presets after initial acquisition and targeting.

[MSI Hole Target queuing](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Queuing_Example_2_-_Hole_Targeting_only): The setup and operation of queuing mode recommanded for quick overall survey of rare hole targets in grid squares.

[Queuing at both levels](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Queuing_Example_3_-_Both_Exposure_and_Hole_Targeting): The setup and operation of queuing mode recommanded for more advanced user who will wait for one operation done before proceeding.

[MSI Trouble shooting](/leginon/Leginon_Manual/Trouble_shooting): This trouble shooting section addresses some of the possible challenges a Leginon user may face while using the MSI application.

[< Flavors of MSI applications](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Flavors_of_MSI_applications) | [Pre-MSI Set-up >](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Pre-MSI_Set-up)
