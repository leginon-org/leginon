## Settings

The settings for this application using standard MSI-T preset is in a json file that should be loaded into leginon database.
The default settings is set to collect 30 degree tilted images.

The main settings that need to be set is the behavior of the tilting.

### Square Node

-   Settings/Tilting> Activate Acquire each target at different tilt in the list
-   Settings/Tilting> Set List of Tiltts to Collect (in degrees) to (0,)

### T Square Node (i.e., Tilted Square)

-   Settings/Tilting> Activate "Acquire all targets in each target list at the same tilt but change to a new tilt at next list".
-   Settings/Tilting> Set List of Tiltts to Collect (in degrees) to the desired tilt angles. For example, (30,) will acquire all images at 30 degrees.

## Operation

-   Acquire grid atlas as usual and select the square as Acquisition Targets.
-   Select both acquisition and focus targets at "T Square Targeting" node. In general, both can be at the center of the square. The focus target selected heret will trigger eucentric adjustment through "Z Focus" node. The acquisition target will trigger image acquisition in "T Square" node.
-   After eucentric height setting by "Z Focus" node, Select and queue up at "T Hole Targeting". See [summary](/leginon/Leginon_Manual/Leginon_MSI-T-Tilt_Application/Summary_of_this_application_-_MSI-T-Tilt) for the recommended target selection pattern. The purpose is to cover 5 holes (1.2/1.3 C-Flat or equivalent) with one of the hole at the center).
-   Test first hole selection in "T Exposure Targeting". We recommend using the center hole for focus This minimize the tilt correction it needs to apply and make the beam tilt autofocus more reliable. See the image shown in [summary](/leginon/Leginon_Manual/Leginon_MSI-T-Tilt_Application/Summary_of_this_application_-_MSI-T-Tilt)

Curently it is not possible to set up automated hole finding for "T Hole Targeting" due to the distortion form tilting. However, it is not too hard to find the center hole in "T Exposure Targeting" and then convolve from it the location of other holes.
