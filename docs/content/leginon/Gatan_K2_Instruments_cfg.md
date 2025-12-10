The camera modes are configured as separate cameras as follows.

-   Super Resolution should be double the size of Linear and Counting.
-   zplane will be relative to any other cameras in your system. Anything below K2 should have a lower zplane.
-   to make the images acquired from the camera to have the [standard Leginon orientation](/leginon/Leginon_Manual/Instrument_Set-up/Leginon_image_orientation), the camera configuration in Digital Micrograph will need a rotation and flip (270 degree rotation and a flip around the vertical axis on our camera) on typical FEI F20 but maybe not so post-GIF or on Krios. Therefore, **the height is longer than width** in the configuration below


    [Gatan K2 Linear]
    class: dmsem.GatanK2Linear
    zplane: 50
    width: 3710
    height: 3838

    [Gatan K2 Counting]
    class: dmsem.GatanK2Counting
    zplane: 50
    width: 3710
    height: 3838

    [Gatan K2 Super]
    class: dmsem.GatanK2Super
    zplane: 50
    width: 7420
    height: 7676

If you have an Orius camera with K2, set its zplane below K2 like this:

    [camera2]
    class: dmsem.GatanOrius
    zplane: 49
    width: 2048
    height: 2048
