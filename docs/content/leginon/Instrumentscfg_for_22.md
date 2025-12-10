### TEM

**cs is the coefficient of spherical aberration in meters**. Find out from TEM manufacture the proper value for your tem.
For example

    [tem]
    class: fei.Tecnai
    cs: 2.0e-3

### Camera

**height and width are number of pixels based on the orientation presented in Leginon image viewer**

-   Some Tietz camera may have an odd physical dimension. Use TCL/EMMenu program to find out the good dimension used in Tietz's own software and entered in this configuration.

For example

    [camera]
    class: gatan.Gatan
    zplane: 50
    height: 4096
    width: 4096

**zplane is a number that gives the order of camera**. If a camera with low zplane value is going to acquire an image, Leginon will attempt to retract all cameras at higher zplane values.

![](images/zplane.png)

**HEIGHT and WIDTH are not shown in these examples for simplicity**

-   One computer for both tem and digital camera:
        [tem]
        class: fei.Tecnai
        cs: 2.0e-3
        [camera]
        class: gatan.Gatan
        zplane: 50


-   Separate computers for the two instruments: configure only the instrument reside on the particular computer
    -   On the computer that controls the tem:
            [tem]
            class: fei.Tecnai
            cs: 2.0e-3
    -   On the computer that controls the digital camera:
            [camera]
            class: gatan.Gatan
            zplane: 50


-   Two camera at the same plane:
    -   On the computer that controls the digital camera:


DE12 and DE Survey camera are retract/extend together, with the survey camera at off-axis. Therefore zplane should be set at the same value
For example,

[camera1]
class: de.DE12
zplane: 50

[camera2]
class: de.DESurvey
zplane: 50


-   Gatan Orius camera that is installed typically with Gatan K2/Falcon camera is technically on the same plane but is not capable of insertion unless K2 is retracted. On the other hand, K2 camera insertion includes a retraction of Orius at lower level of the function call in DM. Therefore, Orius is considered as a camera at lower zplane.
        [camera1]
        class: dmsem.GatanK2Base
        zplane: 50

        [camera2]
        class: dmsem.GatanOrius
        zplane: 49
