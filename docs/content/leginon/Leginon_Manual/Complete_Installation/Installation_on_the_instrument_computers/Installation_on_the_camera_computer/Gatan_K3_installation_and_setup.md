Gatan K3 installation and setup is identical to K2 except the instrument.cfg and the additional dmsem.cfg settings below.

## semccd installation and setup


## Gatan K2/K3 are controlled by a computer separated from the microscope

Please read [Using Leginon on a system where the microscope and camera are controlled by different computers](/leginon/Using_Leginon_on_a_system_where_the_microscope_and_camera_are_controlled_by_different_computers) first.

## Extra Package and Installation

- Use all amd64 version of Windows installer

- SerialEM DigitalMicrograph Plug-in

## SEMCCD Digital Micrograph plug-in installation

Thanks to David Mastronarde for providing his DM plug-in using socket connection

## Note: If you have SerialEM installed on the same computer, you don't have to go through this.  The same Plugin can be used by both programs and share the same port

### Remove your older SEMCCDxxxx.dll in  C:\Program File\Gatan\Plugins if you had it from prevous leginon-only installtion

### Download and extract the files

 1. From your browser, go to [[ https://bio3d.colorado.edu/ftp/SerialEM/FrameAlignment/]]
 2. Choose Shrmemframe*..exe for your version of DM to download to your Gatan PC.
 3. Run the downloaded file and follow its instructions.

Add a new environment variable SERIALEMCCD_PORT if not exist already from SerialEM installation. Set the value to an unused port between 50000 and 60000 to avoid conflict with other programs. Avoid ports [used by Leginon](/leginon/Leginon_Manual/Complete_Installation/Network_Configuration/Ports_used_by_Leginon), especially not 55555.

Port 50000 or 50001 usually works.

![](images/SERIALEMCCD_environment.png)

## instruments.cfg

* A template for instruments.cfg is in the installed pyscope directory as "instruments.cfg.template". Copy it to

C:\Program Files\myami\instruments.cfg

- Remove SimCam modules in the configuration.


## instruments.cfg

* A template for instruments.cfg is in the installed pyscope directory as "instruments.cfg.template". Copy it to


C:\Program Files\myami\instruments.cfg


-   Remove SimCam modules in the configuration.

> **Note:** See [Gatan K3 Instruments.cfg](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Gatan_K3_installation_and_setup/Gatan_K3_Instrumentscfg)

## dmsem.cfg

All available options for K2 are also available to K3. You can configure the section [k2] as described in [Gatan K2 installation and setup](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Gatan_K2_Summit_Support/Gatan_K2_installation_and_setup).
**Make sure you keep the section header [k2]. Don't change that.**

A new section called [k3] includes K3-only settings.

**DM_PROCESSING**

For now, the default is "gain normalized". This means the returned frame movies are dark subtracted and gain normalized. This means the resulting data are float number. Therefore could not be compressed efficiently.

As of today, service mode access is required from Gatan to use K3 in "dark subtracted" mode which is equivalent of the raw-frame movies in K2 counted and super-res mode. This mode can pair with LZW tiff compression to save a lot of space. To do so set the following:

    [k2]
    ....
    SAVE_LZW_TIFF_FRAMES = True
    [k3]
    DM_PROCESSING = dark subtracted

## Testing with pyscope


Binning=2x2 (Counted mode)

# Start DigitalMicrograph

# From python command line or IDLE:

import pyscope.dmsem
k = pyscope.dmsem.GatanK3()
k.setBinning({'x':2,'y':2})
k.setExposureTime(200)
a=k.getImage()
a.shape

- The last command should return the shape of the image arrau

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


