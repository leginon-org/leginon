Tomography node divides the total dose by the number of tilt images it needs to acquire to calculate the real exposure time it uses, given the limit set by the user.
The exposure time, and hence dose, is determined with a formula that takes into account of the fact that the specimen becomes thicker at higher tilts.

The related settings that affect the exposure time per image are:

1.  The dose measurement and exposure time of the preset used as set in Presets Manager. This is used to calculate dose rate.
2.  Total number of images that will be acquired in a tilt series as determined by Tomography Settings/Tilt.
3.  Total dose assigned in Tomography Settings/Misc.

## For a CCD camera, here is an example.

For an analog direct detector that movie will not be processed, the rule is similar, except that you will not see the exposure time change continuously over tilts since they are frame based.

-   Tomo Preset/Exposure Time= 1000 ms
-   Tomo Preset/Dose = 5 e-/A^2

These give dose rate of 5 e/A^2/sec

-   Tomography/Tilt/Min. Angle = --58 degrees
-   Tomography/Tilt/Max. Angle = +58 degrees
-   Tomography/Tilt/Step = 2 degrees

These give a total of 60 tilts appoximately ( Start Angle is taken twice).

As a result the following setting give about 3.3 e/A^2 dose per image (=200/60) and will have an exposure time about 670 ms (=200/60/5). It will be larger at higher tilts but never more than a factor of 2.

-   Tomography/Misc/Total dose=200 e-A^2

This means that you are well within the range if you set the following

-   Tomography/Misc/Exposure time Min.=0.25 seconds
-   Tomography/Misc/Exposure time Max.=2 seconds

## Frame saving camera where frames will be used for drift correction.

We will use K2 counted mode as an example, but it should apply to Falcon and DE camera as well with adjustment for frame time in their context.
**Here is an example that worked well with gold fiducial markers present.**

1. Make sure that you get at least 10 frames for drift correction and enough dose per frame.

-   Tomo Preset/Exposure Time= 1760 ms
-   Tomo Preset/Dose = 0.88 e/A^2 (at 3.25 A/pixel, and what gave ~5.3 e/pixel/s camera dose rate)
-   Tomo Preset/Frame Time = 80 ms

This means dose on camera per frame is 0.425 e/pixel/frame. We figure out this number by trying a few drift alignment at different dose to find a dose that reliably gave us valid alignment with MotionCorr.

2. Set the total dose lower.

-   Tomography/Misc/Total dose=50 e-A^2
-   Tomography/Misc/Exposure time Min.=0.75 seconds (This is set so that we didn't accidental take movie with too few frames.
-   Tomography/Misc/Exposure time Max.=2 seconds (really doesn't matter).

The resulting exposure time in the tilt series ranged from 960 to 1760 ms.

3. Adjust Intensity Scale for Integer output and obstructed count for this:

Each image will have such low counts (5), you probably want to scale this up just so that the sum image looks reasonable, even though they are not used later.

-   Tomography/Misc/Scale to convert to Integer = Yes
-   Tomography/Misc/Scale = 100
-   Tomography/Misc/Obstrcuted count = 100
