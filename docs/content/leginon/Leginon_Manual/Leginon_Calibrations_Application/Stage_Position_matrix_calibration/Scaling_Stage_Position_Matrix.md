High magnification stage position calibration is often difficult if not impossible to perform although it plays a role in determining the orientation of the reference space for image shift targeting between mags.
We will use "Scale Matrix" Tool in Matrix node of Calibration Application (version 3.3 and above) to scale the matrix obtained at "hl" preset to those of higher magnifications.

1.  Send preset to the scope at the magnification a good matrix was calibrated at. The magnification of hl preset is usually good for the purpose if there is no image rotation relative to the higher magnifications you want to scale to.
2.  Click on the "calculator" tool in the toolbar of "Matrix" node. It scales the matrix to all magnifications on this scope above the current mag and save them to the database.

[< Modeled Stage Position calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Modeled_Stage_Position_calibration) | [Checking Matrix and Modeled Stage Position Calibration >](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Checking_Matrix_and_Modeled_Stage_Position_Calibration)
