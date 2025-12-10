Frame saving control through scripting is officially supported with Titan 2.12 and Talos 1.12 version of the microscope software. This should come with Advanced TEM Scripting which is required for Leginon interaction.

## [Installation and testing](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Falcon_3_support)

## To use:

1. Upgrade myami package on the microscope computer to 3.4 version.
2. Setup and test Falcon III integration.
3. Set up en/ef presets in MSI workflow to use the camera.

-   Falcon3EC is the counting activated while the camera name Falcon3 means not counting activated.

## Frame time setup:

Frame time setting is approximate due to Falcon's feature of using a frame for internal reference that is not included in the output. We recommend using TIA interface to find a value pair between number of base rolling-shutter frames per output frame that the software accepts before deciding a usable value as frame time. Also see the next section about restriction when using the internal-drift correction.

For example, enter 25 ms as frame time if you want every rolling-shutter frame to be saved as output frame. This will result in 38 frames in a 1000 ms exposure.

## Falcon III EC internal-drift correction

We recommend turning on Align option in the Leginon preset while using Falcon3EC for final imaging. This activates the internal-frame drift correction within Falcon software and correct drift between the rolling-shutter frame before combining into the longer output frames for the end user.

Because of the algorithm behind the internal-drift correction, each output frame need to include exactly 6 rolling-shutter frames. This is reflected in TUI Camera settings.
For leginon preset settings. Use a frame time of the desired number of rolling-shutter frames.

For example, entering 1050 ms as frame time to get 42 rolling-shutter frames per output frames. In this case, a 47000 ms exposure time gives 44 output frames.
