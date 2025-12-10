## Raster Generation

The settings can be divided into two functions: First, the raster parameters, and second, an raster parameter calculator. The first can function without the second.

Raster Generation/Settings>

-   Bypass Filter = no


-   Verify filter before submitting = yes (turn it off after the setting is stabilized)


-   Convolution Target Type = 'acquisition'


-   Spacing (in number of pixels based on the image where the target comes from)


-   Angle (in degrees clockwise from vertical)

Raster Generation/Settings/Target Raster/Limiting Ellipse>

The algorithm first generate a raster of the above defined spacing and angle, and then use the following parameter to filter the targets whose image touches within the ellipse.

![](images/raster_ellipse.png) For example, the ellipse in this figure has a axis at 1 raster spacing while b axis is 2 raster spacing with angle of 25 deg. Only the images (assuming 0% overlapping and aligned with the raster axes) acquired by the green targets are accepted. Some approximation was involved in this calculation. Therefore the results is not exact. You should experiment with your sample.

-   Angle to a-axis is in degrees and clockwise from vertical

Raster Generation/Settings/Calculator>

-   Raster Preset = hl (This is the preset used in "Final_Section" node)


-   Move Type = 'modeled stage position'


-   Overlap precentage = 0


-   Width (number of points per axis) = 2 (2x2 rasters)

## Section Z Focus Node/Final Section Node

With final targets directly selected from grid atlas, drift management does not function properly. Therefore, all drift managememt functions should be turned off.

Settings/Image Acquisition>

-   Adjust targets using "no" ancestor

## Final Section Node

As the last acquisition node, waiting should be turned off and rejected focus targets should be acquired first.

Settings/Image Acquisition>

-   Wait for a node to process the images = no


-   Publish and wait for rejected targets= yes

[< MSI-Tomography Preferences](/leginon/Leginon_Manual/Preferences_Setup/MSI-Tomography_Preferences)
