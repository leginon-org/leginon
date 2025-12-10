Implementation for using Leginon on JEOL1230 is developed at New York Structural Biology Center directed by David Stokes

The communication is through Serial Port using jeol1230.py and jeol1230lib.py included in Leginon's pyscope subpackage.

There is only one case of installation. Without original instruction, please contact Leginon team if trying this.

### Install 32-bit version of myami package on the associated camera computer

-   Instead of installing myami package on JEOL scope-controlling PC, the access to JEOLCOM usually work through the computer controlling the digital camera, regardless of the camera manufacturer.


-   In addition, the installation is limited to 32-bit version.

## instruments.cfg

[scope]
class: jeol1230.Jeol1230
cs: 2e-3

## Testing with pyscope

In python command

    from pyscope import jeol1230
    t =jeol1230.Jeol1230()
    t.getMagnification()

You should get the current magnification at the microscope at the film camera position

## Calibrations

We do not know if additional calibration is required. The scale calibration done with JEOLCOM scopes is hard coded at the moment. Let us know if it does not work.
