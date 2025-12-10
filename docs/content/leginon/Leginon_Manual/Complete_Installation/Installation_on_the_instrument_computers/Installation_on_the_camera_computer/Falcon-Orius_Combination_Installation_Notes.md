## Install 32 bit versions of the usual Python stuff at python 2.7

## Instruments.cfg


[Falcon Camera]
class:tia.TIA_Falcon
zplane: 50
width: 4096
height: 4096

[Orius]
class:gatan.Gatan
zplane:49
width: 2048
height: 2048

- Note that the class name for Gatan DM controlled camera depends on the number of cameras. Ask us if you have more than one and need to find out which is which.


## Setup

-   Set camera configuration to give the [standard Leginon orientation](/leginon/Leginon_Manual/Instrument_Set-up/Leginon_image_orientation).

## Testing with pyscope

## Trouble shooting ( DO these tests on the camera computer):

### For Falcon camera:

In python command

    form pyscope import tia
    g = tia.TIA_Falcon()
    g.setExposureTime(200)
    g.getImage()

You should get a bunch of numbers in a numpy array. Also, a window should show up in TIA's acquisition gui with the name pyscope

### For Orius (controlled through Gatan DM:

In python command

    form pyscope import tia
    g = gatan.Gatan()
    g.setExposureTime(200)
    g.getImage()

You should get a bunch of numbers in a numpy array.

## Programs to open before Leginon Client: Gatan DM and TIA.
