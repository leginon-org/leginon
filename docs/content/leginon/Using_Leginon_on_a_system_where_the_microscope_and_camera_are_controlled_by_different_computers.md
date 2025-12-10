Newer digital camera often comes with its own Windows PC for faster processing. Leginon can handle this case by having one Leginon Client running on each of the Windows PC. The installation is identical on the two Windows PC except at two places:

-   During [configuration of instrument.cfg in pyscope package](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_microscope_computer):
    -   Only the instrument controlled by the given computer should be added in instrument.cfg.


-   During [importing the Leginon application](/leginon/Leginon_Manual/Administration_Tools/Steps_involved_in_the_installation):
    -   Applications that ends with 2 (i.e. Calibrations2.xml, MSI-T2.xml etc) should be imported from the download. The postfix 2 stands for two Leginon clients,

When Leginon is used, the separated microscope/camera computers are accounted for by including both hosts in the client list and by opening applications that allow Leginon to put separate Instrument nodes on the two hosts. Therefore:

-   Repeat [Run Leginon Client on the Microscope Computer](/leginon/Run_Leginon_Client_on_the_Microscope_Computer) on both Windows computers to allow Leginon to talk to them.
-   Add both Windows PC hosts in the client list when [Start Leginon at your main working station remotely](/leginon/Leginon_Manual/Start_Leginon/Start_Leginon_at_your_main_working_station_remotely)
-   When you need to choose applications as illustrated in [Manual Application Startup](/leginon/Leginon_Manual/Leginon_Manual_Application/Startup) use the application that ends with "2" (i.e. Manual2 instead of Manual)
-   Unlike the illustration in [Manual Application Startup](/leginon/Leginon_Manual/Leginon_Manual_Application/Startup), you will see three launchers that need to be assigned. Assign "Camera" to the camera host and "Scope" to the microscope host.

## How to modify one-client application to be used in this two-client system:

We only made two-client applications that are more popular in the repository. If you need others made, here is the procedure.

1.  Start Leginon and a session on the Linux computer. No clients need to be connected for application editor.
2.  Choose to "Edit" under Application menu bar.
3.  Select the application need to be modified and load.
4.  Change the application name. Convention is to add "2" at the end of the name.
5.  Right click on the application name to add a launcher for camera. i.e., camera
6.  Right click on the new launcher to add a node. Choose EM class as the class of the node and give it an unique alias such as Camera.
7.  Save the application.

## You can add third client in the applications following similar procedure above if you have more camera controlled from different computers. The z-plane values in the instruments.cfg will extend/extract the ones get in the way when camera at lower z-plane is used.
