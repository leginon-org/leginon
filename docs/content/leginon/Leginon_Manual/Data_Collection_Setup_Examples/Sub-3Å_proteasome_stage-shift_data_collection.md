## Instruments

TSRI Krios

1.  Scope: FEI Titan-Krios, 300 kV, micro probe
2.  Camera: Gatan K2. mount directly. 1.21 Å at 29kx scope nominal mag

## Grid

-   1.2/1.3 C-flat carbon support; 400 mesh Copper grid.


Tecnai Krios 300 kV high tension, Gun Lens 5 extraction voltage 4300, 70 um C2 aperture and 100 um objective aperture (except when obtaining grid atlas).
Gatan camera dimension 3710(w)x 3838(h) after rotation to Leginon standard. The size of the beam on the scope main viewing screen always covers the 1.2 um hole at en preset on our scope.
Pixel size is 1.21 A at 22500x scope nominal mag.:

Magnification: Preset name: Image Shift (x,y): Dimension: Binning: Camera Dose (e/camera pixel/s): Exposure Time (ms): Specimen Dose Rate (e/A^2): Spot Size: Defocus (m): C2 (um): frame saving:
------------------------ --------------------- ------------------------------ ------------------ --------------- ---------------------------------------------------------------------------- ------------------------------- --------------------------------------------- ------------------ ------------------------------ --------------- ----------------------
81 gr Aligned 927x959 4 8 100 n/a 10 0.0 70 no
165 sq Aligned 927x959 4 8 100 n/a 9 ---2e-4 70 no
1700 hl Aligned 927x959 4 8 300 0.008 9 ---1.5e-4 70 no
22500 fc 0,0 924x924 2 >=8* 500 8.8 6 ---2.9e-7 70 no
22500 fm 0,0 n/a n/a high n/a high 5 n/a 70 no
22500 fa 0,0 927x959 4 >=8* 200 3.5 6 ---1.5e-6 70 no
22500 en 0,0 7420x7676 1 8 e/physical pixel/s and ~1.9 um on the specimen 7600 36 8 (---1e-6 to ---2e-6) 70 200 ms/frame

- Note: This experiment has an additional preset fm used for melting the ice exclusively. The screen goes down during the melt, therefore, it does not cause radiation damage on the camera. Do not attempt to acquire an image with this preset.

- Note: If the correlation or power spectrum don't work well enough for the standard Camera Dose Rate of 10 e/pixel/s for fc and fa, you may increase it more so not to have to use longer exposure time. The recommended value in literature is meant to give highest DQE at all sampling frequencies. Using a higher camera dose by 50% will certainly not damage the sensor.

- Note: no defocal pair was acquired in this experiment. Therefore, no ef preset.


## Application:

MSI-T2 Advanced (= MSI-T + "Beam Tilt Image" for coma-free alignment + "N2 Filling" for Krios auto nitrogen filler)

## Presets Manager:

No preset cycling (Krios has its own normalization).

## Queuing usage:

Hole Targeting: Queuing, target at the carbon area to cover four holes.
Exposure Targeting: Queuing. manual targeting.

## Move method to reach the targets:

Hole: Presets Manager (modeled) stage position movement
Focus: Presets Manager (modeled) stage position movement
Exposure: [Navigator Iterative movement](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Iterative_Stage_Movement): Target Tolerance: 1e-7 m; Acceptable Tolerance: 3e-7 m

## Wait time before final exposure:

40 seconds
