This data collection obtained same quality data set as stage shift at 1.4x speed with the same presets. More speed gain relative to super-resolution mode data collection. Final reconstruction from the better of the two 3D subclasses (48,000 or ~57,000 cleaned-up particles) gave FSC 0.143 at 2.89 A.

The speed gain relative to previous stage shift data collection is from

1.  removing iterative movement at Exposure node
2.  removing queue processing at Exposure node since both need target adjustment and long wait time before stable imaging.
3.  using counting mode. not super-resolution mode on K2.

**VERY IMPORTANT**: Measure the amount of beam tilt associated with the image-shift at your scope so that it is not compromising the data. Our scope is at 0.3 mrad at the 1.7 um image shift we applied in this experiment.

The Transfer Function will reduce all structure factor to 78% at these beamtilts assuming 0.167 mrad per 1 um image shift:

  ------------------ ---------------------------------------------------------------------------------------
  image shift (um)   45 degree phase modification resolution(0.78 transfer function amplitude) (Angstroms)
  1                  2.4
  2                  3.0
  3                  3.5
  4                  3.8
  ------------------ ---------------------------------------------------------------------------------------

## Instruments

SEMC@NYSBC Krios

1.  Scope: FEI Titan-Krios, 300 kV, micro probe at low mag, nano probe at high mags
2.  Camera: Gatan K2. mount below Falcon/Ceta. 1.21 Å at 29kx scope nominal mag

## Grid

-   1.2/1.3 C-flat carbon support; 400 mesh Copper grid.


- Nanoprobe was used to allow smaller beam to be used for multiple targeting on 2 um hole although not essential in this case.

Tecnai Krios 300 kV high tension, XFEG, Gun Lens 4 extraction voltage 4100, 70 um C2 aperture and 100 um objective aperture (except when obtaining grid atlas).
Gatan camera dimension 3710(w)x 3838(h) after rotation to Leginon standard. The size of the beam on the scope main viewing screen always covers the 1.2 um hole at en preset on our scope.
Pixel size is 1.10 A at 22500x scope nominal mag.:

Probe Lens Series Magnification: Preset name: Image Shift (x,y): Dimension: Binning: Camera Dose (e/camera pixel/s): Exposure Time (ms): Specimen Dose Rate (e/A^2): Spot Size: Defocus (m): C2 (um): frame saving: Camera
---------- ------------------- ------------------------ --------------------- ------------------------------ ------------------ --------------- --------------------------------------------------------------- ------------------------------- --------------------------------------------- ------------------ ------------------------------ --------------- ---------------------- ------------
micro LM 100 gr Aligned 1024x1024 4 n/a 500 n/a 5 0.0 70 no Ceta
micro SA 400 sq Aligned 927x959 4 8 100 n/a 10 ---2e-4 70 no K2
nano SA 1300 hl Aligned 927x959 4 8 200 0.004 11 ---1.5e-4 70 no K2
nano SA 22500 fc 0,0 924x924 2 >=8* 500 3.3 8 ---7e-7 70 no K2
nano SA 22500 fa 0,0 927x959 4 >=8* 250 1.65 8 ---1.5e-6 70 no K2
nano SA 22500 en 0,0 3710x3838 1 8 e/pixel/s and ~0.7 um on the specimen 7000 46 8 (---1e-6 to ---2e-6) 70 200 ms/frame

**These two magnifications are add-on to standard SA lens series made for NYSBC Krios1. May not be available at other scopes.

- Note: If the correlation or power spectrum don't work well enough for the standard Camera Dose Rate of 10 e/pixel/s for fc and fa, you may increase it more so not to have to use longer exposure time. The recommended value in literature is meant to give highest DQE at all sampling frequencies. Using a higher camera dose by 50% will certainly not damage the sensor.

- Note: no defocal pair was acquired in this experiment. Therefore, no ef preset.


## Application:

MSI-T2 Advanced (= MSI-T + "Beam Tilt Image" for coma-free alignment + "N2 Filling" for Krios auto nitrogen filler)

## Presets Manager:

No preset cycling (Krios has its own normalization).

## Queuing usage:

Hole Targeting: Queuing, target at the carbon area to cover four holes.
Exposure Targeting: **No Queuing**. automated targeting. See [Exposure Targeting Set-up for MSi-T for Four Holes](/leginon/Leginon_Manual/Leginon_MSI-T_Application/Exposure_Targeting_Set-up_for_MSI-T_for_Four_holes)

## Move method to reach the targets:

Hole: [Navigator Iterative movement](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Iterative_Stage_Movement): Target Tolerance: 1e-7 m; Acceptable Tolerance: 3e-7 m
Focus: Presets Manager image shift
Exposure: Presets Manager image shift

## Wait time before final exposure chosen to reduce maximal frame drift to average to 2 Angstroms : 3 seconds 10 seconds addition for the first target

## A trick to get Image shift targeting accuracy better:


High magnification stage position calibration is often difficult if not impossible to perform although it plays a role in determining the orientation of the reference space for image shift targeting between mags.

## Use "Scale Matrix" Tool in Matrix node of Calibration Application (version 3.3 and above)

1. Send preset to the scope at the magnification a good matrix was calibrated at. The magnification of hl preset is usually good for the purpose if there is no image rotation relative to the higher magnifications you want to scale to.
2. Click on the "calculator" tool in the toolbar of "Matrix" node. It scales the matrix to all magnifications on this scope above the current mag and save them to the database.

## Manual Edit (version 3.2 and below)

Get a better estimate of stage position matrix at en magnification by scaling the matrix at hl mag.
You can find the matrix in image report (Click on the "i" in the myamiweb [imageviewer image tools bar](/leginon/Leginon_Manual/Leginon_Manual_Application/Using_the_Web_viewer/Common_Features))

### Scale the matrix by magnification will give a reasonable value.

For example, if your hl preset at 1300x has a matrix of

2e-9 --6e-9
--6e-9 --2e-9


Then a good estimate of the matrix for your en preset at 22500x would be multiplied by 1300 / 22500 and becomes

1.16e-10 --3.47e-10
--3.47e-10 --1.16e-10

### You can enter the result directly in Calibration application Matrix node using "Edit" tool at the toolbar after the required preset is sent.


