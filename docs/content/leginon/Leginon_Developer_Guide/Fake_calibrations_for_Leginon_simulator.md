Read the instruction for real Calibration Application on details like how to load application, entering the values which I will not repeat here.

## Create presets:

1.  A highly binned camera configuration such as 512 binned by 8 is sufficient.
2.  As a short cut you can use the same magnification for all presets. If using more magnifications, you will have to calibrate them, too.
3.  Always send the preset with the magnification you want to "calibrate" first "to Scope".

## Pixel Size Calibration:

1.  Enter Calibration for 50000x as 2e-10 m/pixel
2.  Extrapolate the pixel size to all other simulated magnifications

## Matrix Calibration:

1.  Use Edit Calibration Tool, you can enter directly the calibration matrix. For example, my standard matrix for 50000x looks like this:
        2e-10      0
        0          2e-10

    
    You will want to scale it down for lower magnification. For example, the one for 5000x should have 10 x in values at each matrix element.

## Beam Tilt related Calibration:

1.  Just go through the defocus calibration as if it is a real scope/camera is good enough.

## Dose (Camera Sensitivity) Calibration:

1.  Enter Camera Sensitivity of some value such as 5 counts/electron.

### You may need to increase tolerance of some of the error check in the application you run, but, otherwise, you should be good to test if you have bugs in your development that will cause a crash.
