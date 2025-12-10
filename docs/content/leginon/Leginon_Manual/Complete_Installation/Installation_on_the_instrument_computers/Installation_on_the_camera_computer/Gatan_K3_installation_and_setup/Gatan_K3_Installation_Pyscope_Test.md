Binning=2x2 (Counted mode)

# Start DigitalMicrograph

# From python command line or IDLE:

    import pyscope.dmsem
    k = pyscope.dmsem.GatanK3()
    k.setBinning({'x':2,'y':2})
    k.setExposureTime(200)
    a=k.getImage()
    a.shape

-   The last command should return the shape of the image arrau


You should expect these to run without error. The getImage() command should give a 2D numpy array like

array([[1000, 3400, 2300, ..., 1000,1200,3000],
[1000, 3400, 2300, ..., 1000,1200,3000],
[1000, 3400, 2300, ..., 1000,1200,3000],
...,
[1000, 3400, 2300, ..., 1000,1200,3000],
[1000, 3400, 2300, ..., 1000,1200,3000],
[1000, 3400, 2300, ..., 1000,1200,3000],dtype=int16)

The number and dtype depends on the camera.

a.shape command should give a tuple of the camera dimension matching your camera.
For example, (4096,4096)

**If you use python shell to do this test, some of the error will cause the shell window to close immediately. Use Python IDLE instead in that case**


#### Testing frame saving

You can continue the test above by saving frames, too.


k.setSaveRawFrames(True)
k.setExposureTime(200)
a=k.getImage()
a.shape

- The last command should give you the shape of the summed image, and the frame movie should show up on your frames directory


