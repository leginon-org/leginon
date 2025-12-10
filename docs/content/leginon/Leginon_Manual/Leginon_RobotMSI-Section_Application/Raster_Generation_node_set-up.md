The Raster Generation node belongs to Raster Target Filter Class. It accepts a list of targets and then convolving each with a raster of targets.

## Initial Preference Setup

The settings can be divided into two functions: First, the raster parameters, and second, an raster parameter calculator. The first can function without the second.

Raster Generation/Settings>

-   Bypass Filter = no


-   Verify filter before submitting = yes (turn it off after the setting is stabilized)


-   Convolution Target Type = 'acquisition'


-   Spacing (in number of pixels based on the image where the target comes from)


-   Angle (in degrees clockwise from vertical)

Raster Generation/Settings/Target Raster/Limiting Ellipse>

The algorithm first generate a raster of the above defined spacing and angle, and then use the following parameter to filter the targets whose image touches within the ellipse.

![](images/raster_ellipse.png)

For example, the ellipse in this figure has a axis at 1 raster spacing while b axis is 2 raster spacing with angle of 25 deg. Only the images (assuming 0% overlapping and aligned with the raster axes) acquired by the green targets are accepted. Some approximation was involved in this calculation. You should experiment with your sample.

-   Angle to a-axis is in degrees and clockwise from vertical

Raster Generation/Settings/Calculator>

-   Raster Preset = hl (This is the preset used in "Final_Section" node)


-   Move Type = 'modeled stage position'


-   Overlap precentage = 0


-   Width (number of points per axis) = 2 (2x2 rasters)

## Select raster parameter on the first set of test section images

The raster generation settings can be verified with the option activated. If there are uncertainty in the raster spacing and angle, it is worth testing with small rasters and view the results on web image viewers.

1.  Raster Generation> Give a guessed spacing and angle with a small number of points.
2.  Grid Center Targeting> [Selecting one position as center of the raster on the grid atlas](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_Operation#Select-Squares-on-the-atlas) and submit
3.  Web 3wviewer>View the resulting hl images and its marking on its parent gr image to adjust raster parameters for desired overlap and raster width.
4.  Raster Generation> Adjust the raster spacing and angle.
    bq. Once some targets have passed through the node, you can use the raster calculator to get the spacing and angle based on the raster preset and overlap percentage. (If the result raster looks very wrong on the Web Image viewer based on the calculation, try to inverse the angle (i.e., multiply by --1). We don't know why some work and some don't.)
5.  Repeat 2-4 until satisfied.

## Editing targets on the subsequent images

If the ellipse does not follow the tissue of interest, manual editing of the raster points can be made with verification activated. Leginon will pause after each raster of targets is made. You can then right click to remove or left click to add targets. Click on Submit button to acquire images of the final target raster or click stop to abort data acquisition of these targets.

[< Summary of this application](/leginon/Leginon_Manual/Leginon_MSI-Edge_Application/Summary_of_this_application) | [Other special preference set-up >](/leginon/Leginon_Manual/Leginon_RobotMSI-Section_Application/Other_special_preference_set-up)
