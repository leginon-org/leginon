This tool in "Navigation" node (icon looks like a ruler) repeatly attempt to reach the current stage position by sending its coordinates to scope from a defined remote location.
It displays the offset it arrive at in the logger window.

The dialog looks like this:

![](images/StageReproducibilityDialog.png)

-   **Label**: This is used to identify the test run in the database within the session. There is no file output for this test.
-   **Moves**: Number of test repeats
-   **Distance**: Radius to move away and back in meters
-   **Angle**: If left blank, the remote location will be at a random direction, different each time. If specified, the angle will be fixed.

**Note** The move requires no Leginon calibration but the physical distance shown in the offset log would be affected by the pixel size calibration.
