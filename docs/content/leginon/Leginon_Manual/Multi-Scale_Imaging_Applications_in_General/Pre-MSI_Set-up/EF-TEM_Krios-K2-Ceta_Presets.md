Tecnai Krios 300 kV high tension always in EF-TEM mode, Gun Lens 5 extraction voltage 4300, 70 um C2 aperture and 100 um objective aperture (except when obtaining grid atlas).
Gatan camera dimension 3710(w)x 3838(h) after rotation to Leginon standard. The size of the beam on the scope main viewing screen always covers the 1.2 um hole at en preset on our scope.

Pixel size is 1.06 A at 130,000x scope nominal mag.:

  Magnification:   Preset name:   Image Shift (x,y):   Dimension:                   Binning:   Camera Dose (e/camera pixel/s):                     Exposure Time (ms):   Specimen Dose (e/A^2):   Spot Size:   Defocus (m):         C2 (um):   frame saving:
  ---------------- -------------- -------------------- ---------------------------- ---------- --------------------------------------------------- --------------------- ------------------------- ------------ -------------------- ---------- ---------------
  1550             gr             Aligned              1024x1024(Taken with Ceta)   4          ?                                                   250                   n/a                       4            0.0                  70         n/a
  940              sq*           Aligned              927x959                      4          8                                                   400                   n/a                       9            --2e-4               70         no
  3600             sq*           Aligned              927x959                      4          8                                                   100                   n/a                       9            --5e-5               70         no
  8700             hl             Aligned              927x959                      4          8                                                   300                   0.008                     7            --6e-5               70         no
  22500            fc             0,0                  924x924                      2          >=8*                                              500                   8.8                       7            --2.9e-7             70         no
  22500            fm*           0,0                  n/a                          n/a        high                                                n/a                   high                      5            n/a                  70         no
  130000           fa             0,0                  927x959                      4          >=8*                                              200                   3.5                       6            --1.5e-6             70         no
  130000           en             0,0                  3710x3838                    1          8 e/physical pixel/s and ~1.3 um on the specimen   6000                  43                        7            (--1e-6 to --2e-6)   70         200 ms/frame

-   Note about sq preset: Depending on the alignment of the scope in EF-TEM, the beam at lowest SA mag may not expand enough without losing zero-loss peak. We have tried on different scopes either using a mag in LM mode (940x) and another at higher mag SA mode (3600x). Each has pro and con. 940x has more image-shift hysteresis but gives a full grid square. 3600x has a rather small imaging area that makes determining exposed area difficult. For 3600x, we may use a medium mag stitch application similar to MSI-PP-Stitch.


-   Note: This experiment has an additional preset fm used for melting the ice exclusively. The screen goes down during the melt, therefore, it does not cause radiation damage on the camera. Do not attempt to acquire an image with this preset.


-   Note: If the correlation or power spectrum don't work well enough for the standard Camera Dose Rate of 10 e/pixel/s for fc and fa, you may increase it more so not to have to use longer exposure time. The recommended value in literature is meant to give highest DQE at all sampling frequencies. Using a higher camera dose by 50% will certainly not damage the sensor.


-   Note: no defocal pair was acquired in this experiment. Therefore, no ef preset.
