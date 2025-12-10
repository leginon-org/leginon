## [Enter Grid Information](/leginon/Leginon_Manual/Leginon_Robot-MSI-Screen_Applications/Upload_Grids) through Project Web Form

1.  Go to http://your_host/myamiweb/project/project.php on a web browser.
2.  Select the Grid Tray Panel.
3.  Click on upload grids/tray

-   Follow the format and instruction to create an upload file with grid information with labels unique to the project and location unique to the grid box to be inserted.

## Set up robot and grids in its tray matching your entry

**Leginon does not know if you switch grids and pretend!**

## Start Leginon

-   This include general scope alignment and preset alignement

## [1st Pass Screening](/leginon/Leginon_Manual/Leginon_Robot-MSI-Screen_Applications/1st_Pass_application)

1.  Starting node is the Robot node
2.  Enter in the settings the stage z value that will give the approximate eucentric height for the holder used.
3.  Select the robot tray
4.  Select grids in the Robot node and click "Start". You might need to click "Continue". too. It is a bug that is hard to remove without causing other problems. Right click removes a selection. Middle click displays the selected grid label
    **The grids are imaged in the order of the grid selection.**
5.  Activate user verification in "Square Targeting" and "Mid Mag Survey Targeting" nodes
6.  Use the first grid to optimize square finding and raster sizing and angles and then remove the user verification for full automation.

-   For "Square Targeting", optimize to find all grid squares with intact support film and proper stain.
-   "Square Target Filtering" is default to find the center-most of the selected targets pass into it.
-   "Mid Mag Survey Targeting" is best set to spread out the targeting position.

## [Evaluation](/leginon/Leginon_Manual/Leginon_Robot-MSI-Screen_Applications/Evaluation_application)

1.  Start the application under the same Leginon session. Microscope and robot not required by this application.
2.  Choose "hl" or "sq" preset as the child and "gr" preset as ancestor.
3.  Click next to get the first image.
4.  Choose targets and then click on "Transform" tool.
    **Do not forget to transform if you modify the targets.**
5.  Continue to "next" image until at the end.
6.  Select targets at the other child preset, too.

## [2nd Pass Screening](/leginon/Leginon_Manual/Leginon_Robot-MSI-Screen_Applications/2nd_Pass_application)

-   Starting the sequence at "2nd Pass Targeting" under the same session with mircoscope and robot ready.
-   If no modification is needed after evaluation step, just "Submit" the targets to initiate the process which will pause to wait for confirmation that the robot is ready to start.

[< Summary of these applications](/leginon/Leginon_Manual/Leginon_Robot-MSI-Screen_Applications/Summary_of_this_application_-_Robot-MSI-Screen) | [Grid Registration >](/leginon/Leginon_Manual/Leginon_Robot-MSI-Screen_Applications/Upload_Grids)
