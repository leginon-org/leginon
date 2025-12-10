-   ![](images/notes.png) Manual/Toolbar/Annotation> Comments about the images can be attached to the image and displayed in ImageViewer. It can be made to pop up after each image is acquired by checking the "Always Annotate Saved Images" in the settings.


-   ![](images/dose.png) Manual/Toolbar/Measure Dose> In Exposure mode, if low dose kit is used, and at a location that is free of scattering matter, you can measure the dose in electrons/angstrum^2 at the current setting using the "Measure Dose" tool. A CCD image no larger than 512x512 will be taken using the exposure time specified in the Setting Window.


-   ![](images/manualfocus.png) Manual/Toolbar/Live FFT> for manual focusing: Using current TEM setting, this tool acquires continuously images at 0.1 sec exposure time and at the center 512x512 pixels of the CCD with power spectrum displayed.


-   ![](images/loop_play.png) Manual/Toolbar/Continuous Acquire> Using current setting to acquire series of images, paused in between by the time defined in the settings.


-   ![](images/grid.png) Manual/Toolbar/Grid>: Open "Grid" tool to select the grid used in the microscope if project database is used and if the grid information is entered in the database. This option is inactive without the project database.


-   Manual/Settings/Label=any label that will be attached to the image in the database. Intended for identifying the grid. Currently, a MySQL query needs to be perform to use the label. Leave it blank if you don't care to use one. We recommend using Annotation tool instead.


-   Power Spectrum> You may activate automatic power spectrum calculation of the acquired image here in the settings window. By defaul, the spectrum is limited to the center 1024x1024 pixels.

[< Running "Manual" Application](/leginon/Leginon_Manual/Leginon_Manual_Application/Running_Manual_Application) | [Using the Web viewer >](/leginon/Leginon_Manual/Leginon_Manual_Application/Using_the_Web_viewer)
