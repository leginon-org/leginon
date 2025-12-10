Picoammeter setup:

-   plug in
-   wait 1 hour
-   activate ZCHK (maybe already when turned on) (should say ZC on screen)
-   plug into faraday holder
-   set to lowest range (2nA)
-   activate ZCOR to set zero (should say ZZ on screen)
-   set auto range if desired
-   deactivate ZCHK to begin measuring
-   focus beam to a spot
-   pull out holder until spot hits the faraday cup (max current) (This is a negative value)
    Examples
    -   200keV
        -   1.21 nA
    -   120 keV
        -   2.53 nA

# Exposure Time to Screen Current measurment

-   refer to Tecnai Help for "Exposure Time, Plate Camera CP"
-   formula: beam current (nA) = 2.15 * emulsion / measured_exposure_time
    -   exp time is between 3.1 and 3.5 depending on size of beam
    -   emulsion = 1
    -   beam current is between 0.61 and 0.69 nA

# Leginon screen scale factor measurement

-   adjust scale factor until beam current is same as faraday cup
    -   200 keV
        -   0.725
    -   120 keV

# Camera sensitivity

200 keV

* 45-50 count/e

120 keV

* 107 count/e

# 2011-02-02 calibration on Tecnai 2:

-   faraday measurement: 1.52 nA
-   Tecnai main screen measurement (emulsion = 1): 2.15 / 2.6 = 0.83 nA
-   Leginon scale factor to match faraday current: 0.793
-   Legion measures Tietz sensitivity: 68.7 counts/e-

# 2013-02-28 Calibration on T12 Spirit

-   120kV, Filament Heat= 29, step 1, Spot 3, mag 46K, Beam Current = 5.5-7.5 µA, LaB6 installed 2013-02-22
-   TVIPS F416 camera
-   Technai main screen measurement (emulsion = 1): 2.15 / 0.11 = 19.54 nA
-   Leginon scale factor to match Faraday current: 0.991 (was 0.80)
-   Leginon measure Tietz sensitivity: 38.8294 counts/e- (was 32.5211)

# Finding the Faraday Cup

-   See picture below
-   Center to cup is 4mm
-   Use a 6mm or 7mm Allen (hex) wrench as a wedge (spacer) between the holder end cap and stage. Use the wrench as a lever to fine tune the position
