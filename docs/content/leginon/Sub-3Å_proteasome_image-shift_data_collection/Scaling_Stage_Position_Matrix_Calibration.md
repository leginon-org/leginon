High magnification stage position calibration is often difficult if not impossible to perform although it plays a role in determining the orientation of the reference space for image shift targeting between mags.

## Use "Scale Matrix" Tool in Matrix node of Calibration Application (version 3.3 and above)

1.  Send preset to the scope at the magnification a good matrix was calibrated at. The magnification of hl preset is usually good for the purpose if there is no image rotation relative to the higher magnifications you want to scale to.
2.  Click on the "calculator" tool in the toolbar of "Matrix" node. It scales the matrix to all magnifications on this scope above the current mag and save them to the database.

## Manual Edit (version 3.2 and below)

Get a better estimate of stage position matrix at en magnification by scaling the matrix at hl mag.
You can find the matrix in image report (Click on the "i" in the myamiweb [imageviewer image tools bar](/leginon/Leginon_Manual/Leginon_Manual_Application/Using_the_Web_viewer/Common_Features))

### Scale the matrix by magnification will give a reasonable value.

For example, if your hl preset at 1300x has a matrix of

     2e-9  -6e-9
    -6e-9  -2e-9


Then a good estimate of the matrix for your en preset at 22500x would be multiplied by 1300 / 22500 and becomes

     1.16e-10 -3.47e-10
    -3.47e-10 -1.16e-10

### You can enter the result directly in Calibration application Matrix node using "Edit" tool at the toolbar after the required preset is sent.
