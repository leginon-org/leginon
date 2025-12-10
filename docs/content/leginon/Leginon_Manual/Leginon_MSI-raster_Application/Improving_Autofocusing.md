Because MSI-raster is normally used for acquiring images on negatively stained particles on continuous carbon, the intermediate mag preset (hl) often lacks contrast. To reduce focusing failure, we recommend a different focusing sequence for the Z focus node.

-   Use Stage Alpha Tilt to determine defocus at the low magnification sq preset to do a rough stage-z adjustment to U-center


-   Refine stage-z position at the high magnification fa preset and Use beam-tilt to determine the required correction.

For "Stage_Wobble" Step:

-   Enable = Yes


-   Image registration= phase correlation


-   Fit limit = 1000 (not used)


-   Correct for delta Defocus/Z between 0 and 2e-4 meters


-   Correction type = Stage Z


-   Check drift greater than 3e-10 meters/s = No


-   Stigmator correction = No


-   Stigmator Defocus Max/Min = N/A

For "Z_to_Eucentric" Step, change these:

-   preset = fa


-   Correct for delta Defocus/Z between 0 and 2e-5 meters

[< Queuing Option](/leginon/Leginon_Manual/Leginon_MSI-raster_Application/Queuing_Option_-_MSI-raster)
