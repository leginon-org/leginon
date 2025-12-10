## Design Presets

To start your own MSI experiment, you must decide what presets you want to use. Presets are used to define scope and camera parameters with which images are acquired.

MSI presets can be customized to your need of data collection. By matching nodes/subnodes in MSI with presets and move types, the behavior of the node is defined. **Please do not use "-" in preset name** It is reserved for frame aligned sum preset labeling.

For easy reference and for preloading node settings in the our distribution, preset names in MSI has been standardized at NRAMM. **We strongly advice that you use these to start with so that the default settings will work right away**. You can use other names when you become advanced user and are comfortable changing settings. They are abbreviated to 2 letter codes to reduce the length of the filenames that contains every preset used in its family history.

Example MSI preset nomenclature:

  Preset name:   abbrev for:     in the context of:
  -------------- --------------- ------------------------------------------------------
  gr             grid            em grid
  sq             square          em grid square
  hl             hole            quantifoil hole
  fc             focus           focus image to be checked with fft
  fa             focus-auto      automatic focusing
  en             exposure-near   close-to-zero defocus exposure image in a focal pair
  ef             exposure-far    far-from-zero defocus exposure image in a focal pair

Example MSI preset parameters (based on 120 or 200 kV high tension, 100 um C2 aperture and 100 um objective aperture on a 4k ccd with pixel size at 1.6 angstrom at scope nominal magnification of 50,000x):

  Magnification:   Preset name:   Image Shift (x,y):   Dimension:   Binning:   Beam Coverage:   Exposure Time (ms):   Spot Size:   Defocus (m):
  ---------------- -------------- -------------------- ------------ ---------- ---------------- --------------------- ------------ --------------
  120              gr             Aligned              512          8          max              20                    4            0.0
  550              sq             Aligned              1024         4          1x CCD size      100                   4            --2e-3
  5000             hl             Aligned              512          8          1x CCD           20                    4            --1.5e-4
  50000            fc             0,0                  512          1          <~ 1x CCD      300                   4            --2e-6
  50000            fa             0,0                  1024         4          >2x CCD         50                    4            --2e-6
  50000            en             0,0                  4096         1          2x CCD           170 (10e/A^2)        4            --1e-6
  50000            ef             0,0                  4096         1          2x CCD           170 (10e/A^2)        4            --2e-6

The preset parameters in this example are chosen to give the following properties:

-   **en** and **ef** are for final exposures and therefore have highest resolution and dimension.


-   **en** stands for near focus exposure and therefore has lower defocus value than **ef**,the far-from-focus exposure.


-   **fa** is for high resolution autofocus and therefore need to be high mag. The dimension and binning is a result of compromising speed, S/N ratio and sensitivity to
    details.


-   **fc** is for manual focus and ice melting and therefore more intense than **fa**. To get good FFT for checking Thon ring behavior, it is not binned. The small dimension is for increasing speed.


-   **hl** is for intermediate targeting. It needs to cover the error range of modeled stage position to allow final targeting by image shift only, hence the magnification. The binning is for speed.


-   **sq** is for grid square targeting. The image produced by the preset ideally need to cover most if not all of the square but with enough resolution to evaluate the content. However, the first priority is to **choose a magnification at which no aperture used during the data collection will limit much of the illuminated area on the CCD**. If too much of the area is obstructed, target adjustment critical to MSI operation will fail. The coverage of the grid square can always be achieved by choosing multiple targets on it.


-   **gr** is for producing grid atlas. It is selected based on the size number of tiles needed to cover the whole grid in an acceptable time and the amount of distortion common to very low mag imaging. Objective aperture can be removed and a larger C2 aperture used while using this preset to acquire grid atlas. It is never used after the atlas is acquired.

In designing your own preset, follow the above properties using a mag that gives the required coverage with your scope, camera, and grid mesh. If you have a 2k or 1k camera, binning may not be as necessary as for a 4k camera whose data acquisition time is 10-30 sec without binning.

## Another Recent Preset Design Example (Rotavirus 4.4 A resolution, Cambell et. al., *Structure*(2012))

Tecnai F20 200 kV high tension, Gun Lens 3 extraction voltage 4300, 50 um C2 aperture and 100 um objective aperture (except when obtaining grid atlas).
Camera is a Tietz F415 4k ccd with pixel size at 1.6 angstrom at scope nominal magnification of 50,000x for lower mag MSI and focusing, and a Direct Electron DE-12 4kx3k direct detection camera for final exposure (ed preset):

  Magnification:   Preset name:   Image Shift (x,y):   Dimension:   Binning:   Beam Coverage:           Exposure Time (ms):   Dose (e/A^2):   Spot Size:   Defocus (m):         C2 (um):
  ---------------- -------------- -------------------- ------------ ---------- ------------------------ --------------------- ---------------- ------------ -------------------- ----------
  120              gr             Aligned              512          8          max                      20                    n/a              4            0.0                  100
  1700             sq             Aligned              1024         4          1x CCD size              10                    n/a              4            --2e-4               50
  5000             hl             Aligned              1024         4          1x CCD                   7                     0.004            4            --1.5e-4             50
  100000           fc             0,0                  512          2          <~ 1x CCD              200                   164              4            --2.9e-7             50
  100000           fa             0,0                  1024         4          ~4x CCD                 50                    2.5              4            --1.5e-6             50
  100000           en             0,0                  4096         1          1.3 um on the specimen   407                   20               4            (--1e-6 to --2e-6)   50
  29000            ed             0,0                  3kx4k        1          1.3 um on the specimen   407                   20               4            (--1e-6 to --2e-6)   50

-   Note: This experiment used direct detection camera for final exposure (ed preset). en preset was not used in the actual experiment. It is here just for reference and to show what we would have used if recorded on CCD based on our GroEL study. During process, the final images for en would have been binned by 2 based on our experience so the en preset could have being collected at 2048 binned by 2.


-   Note: no defocal pair was aquired in this experiment. Therefore, no ef preset.

## Preset Design Example for Falcon II on Krios

Tecnai Titan Krios 300 kV high tension, Gun Lens 3 extraction voltage 4150, 70 um C2 aperture and 100 um objective aperture (except when obtaining grid atlas).
Falcon II mounted with Gatan Orius as the secondary camera. Pixel size at 1.4 angstrom at scope nominal magnification of 59,000x (ed preset).
The c-flat grid used in this has 1.2 um holes. One image is taken at each hole.

  Magnification:   Preset name:   Camera:   Image Shift (x,y):   Dimension:   Binning:   Beam Coverage:           Exposure Time (ms):   Dose (e/A^2):   Spot Size:   Defocus (m):         C2 (um):
  ---------------- -------------- --------- -------------------- ------------ ---------- ------------------------ --------------------- ---------------- ------------ -------------------- ----------
  40               gr             Orius     Aligned              1024         4          max                      100                   n/a              10           0.0                  70
  1700             sq             Falcon    Aligned              1024         4          1x CCD size              100                   n/a              10           --5e-4               70
  3800             hl             Falcon    Aligned              1024         4          12 um                    300                   n/a              10           --2e-4               70
  45000            fm             Orius     0,0                  1024         2          small                    500                   100              7            --2.9e-7             70
  75000            fc             Orius     0,0                  1024         2          0.5 um on the specimen   500                   164              6            --2.9e-7             70
  75000            fa             Falcon    0,0                  1024         4          1.2 um on the specimen   200                   2.5              7            --1.5e-6             70
  59000            en             Falcon    0,0                  4kx4k        1          1.3 um on the specimen   2000                  45               6            (--1e-6 to --2e-6)   70

-   fm is the melting preset. No image is taken with this. The preset is used only to set microscope parameters. The camera is set to Orius as extra protection.
-   Frames are saved in ed preset with (1,2,17) set in "Frames to use" field, giving 22.5 e/A^2 total dose in the movie that is used for image processing and volume reconstruction.

## Preset Design Example for small pixel Gatan K2 camera alone


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



Magnification: Preset name: Image Shift (x,y): Dimension: Binning: Camera Dose (e/camera pixel/s): Exposure Time (ms): Specimen Dose Rate (e/A^2): Spot Size: Defocus (m): C2 (um): frame saving:
------------------------ --------------------- ------------------------------ ------------------ --------------- --------------------------------------------------------------- ------------------------------- --------------------------------------------- ------------------ ------------------------------ --------------- ----------------------
80 gr Aligned 927x959 4 10 100 n/a 5 0.0 100 no
800 sq Aligned 927x959 4 10 100 n/a 3 0.0 50 no
2500 hl Aligned 927x959 4 10 400 0.008 4 ---2e-5 50 no
2500 hc Aligned 927x959 4 10 400 0.008 4 ---2e-5 50 no
25000 fc 0,0 926x926 2 >=10* 400 8.8 4 ---2.9e-7 50 no
25000 fm 0,0 n/a n/a high n/a high 4 n/a 50 no
25000 fa 0,0 927x959 4 >=10* 200 3.5 4 ---1.5e-6 50 no
30000 ed 0,0 3710x3838 1 8 e/pixel/s and ~1.3 um on the specimen 5000 27 4 (---1e-6 to ---2e-6) 50 200 ms/frame

- Spot 5 on this scope is modified by JEOL engineers to reduce the beam intensity further from the original values so that it does not over dose K2 sensor.
- The strong image shift hysteresis of the 800x square preset required us to use MSI application that has an extra step of centering the holes using 2500x mag. See [Leginon Operation for JEM scopes#Special-MSI-Application-designed-to-avoid-using-LOWMAG-sq-preset-in-the-target-adjustment](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_microscope_computer_30/JEOLCOM_installation_specifics/Leginon_Operation_for_JEM_scopes#Special-MSI-Application-designed-to-avoid-using-LOWMAG-sq-preset-in-the-target-adjustment)


## Preset Design Example for FEI Krios EF-TEM


Tecnai Krios 300 kV high tension always in EF-TEM mode, Gun Lens 5 extraction voltage 4300, 70 um C2 aperture and 100 um objective aperture (except when obtaining grid atlas).
Gatan camera dimension 3710(w)x 3838(h) after rotation to Leginon standard. The size of the beam on the scope main viewing screen always covers the 1.2 um hole at en preset on our scope.

Pixel size is 1.06 A at 130,000x scope nominal mag.:

Magnification: Preset name: Image Shift (x,y): Dimension: Binning: Camera Dose (e/camera pixel/s): Exposure Time (ms): Specimen Dose (e/A^2): Spot Size: Defocus (m): C2 (um): frame saving:
------------------------ --------------------- ------------------------------ ------------------------------------------ --------------- ---------------------------------------------------------------------------- ------------------------------- ------------------------------------- ------------------ ------------------------------ --------------- ----------------------
1550 gr Aligned 1024x1024(Taken with Ceta) 4 ? 250 n/a 4 0.0 70 n/a
940 sq* Aligned 927x959 4 8 400 n/a 9 ---2e-4 70 no
3600 sq* Aligned 927x959 4 8 100 n/a 9 ---5e-5 70 no
8700 hl Aligned 927x959 4 8 300 0.008 7 ---6e-5 70 no
22500 fc 0,0 924x924 2 >=8* 500 8.8 7 ---2.9e-7 70 no
22500 fm* 0,0 n/a n/a high n/a high 5 n/a 70 no
130000 fa 0,0 927x959 4 >=8* 200 3.5 6 ---1.5e-6 70 no
130000 en 0,0 3710x3838 1 8 e/physical pixel/s and ~1.3 um on the specimen 6000 43 7 (---1e-6 to ---2e-6) 70 200 ms/frame

- Note about sq preset: Depending on the alignment of the scope in EF-TEM, the beam at lowest SA mag may not expand enough without losing zero-loss peak. We have tried on different scopes either using a mag in LM mode (940x) and another at higher mag SA mode (3600x). Each has pro and con. 940x has more image-shift hysteresis but gives a full grid square. 3600x has a rather small imaging area that makes determining exposed area difficult. For 3600x, we may use a medium mag stitch application similar to MSI-PP-Stitch.

- Note: This experiment has an additional preset fm used for melting the ice exclusively. The screen goes down during the melt, therefore, it does not cause radiation damage on the camera. Do not attempt to acquire an image with this preset.

- Note: If the correlation or power spectrum don't work well enough for the standard Camera Dose Rate of 10 e/pixel/s for fc and fa, you may increase it more so not to have to use longer exposure time. The recommended value in literature is meant to give highest DQE at all sampling frequencies. Using a higher camera dose by 50% will certainly not damage the sensor.

- Note: no defocal pair was acquired in this experiment. Therefore, no ef preset.


## Calibrations

If this is the first time Leginon is used under the scope-camera combination at the preset magnifications, complete all the calibrations listed in [the chapter on calibrations](/leginon/Leginon_Manual/Leginon_Calibrations_Application). Calibrations are extremely important to operate the TEM in a consistent manner. As long as the calibrations are stable, later users do not need to perform them. Most calibrations are HT and magnification dependent. Therefore, new calibration may be required if your presets use different HT and/or magnification from all previous users.

[< Summary of MSI applications](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Summary_of_MSI_applications) | [Initial MSI application preferences >](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Initial_MSI_application_preferences)
