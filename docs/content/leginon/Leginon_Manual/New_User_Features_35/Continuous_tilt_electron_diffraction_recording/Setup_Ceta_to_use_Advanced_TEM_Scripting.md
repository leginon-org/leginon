Diffraction mode image acquisition is not available through TIA Scripting. Advanced TEM Scripting must be used.

**At this point, only one camera can be controlled through Advanced TEM Scripting. If the system has both Falcon and Ceta camera, Falcon camera has to be removed from instruments.cfg and Ceta camera should use feicam rather than tia python module in instruments.cfg.**

We recommend that you estabilish protocol to switch instruments.cfg used for MSI imaging that requires Falcon camera to the diffraction recording that uses Ceta camera only.

## Example of proper instruments.cfg for diffraction recording. This need to replace the one using tia module.

The exact module name (cetacam in this example) is not important. They just need to be unique. Class name needs to be exact match to the actual class.
If your instruments.cfg contains tia.TIA_Ceta, you should comment it out. This replacement of the instrument makes it unnecessary to recalibrate.

    [cetacam]
    class: feicam.Ceta
    zplane: 50
    height: 4096
    width: 4096

## Programs to open before Leginon Client: TIA.

## Testing with pyscope

In python command

    from pyscope import feicam
    g = feicam.Ceta()
    g.setExposureTime(200)
    g.getImage()


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


