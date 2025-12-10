The TEM Advanced Scripting required to interface with Falcon 4 is officially available with TFS software version 3.6 and above. For earlier version, request a patch from TFS will allow you to use mrc frame movie saving.

Since the non-counting mode of Falcon4 requires too bright a beam to operate, only counted mode is implemented for this camera.

The instruments.cfg class to be included is

    [falcon4]
    class: feicam.Falcon4EC
    zplane: 50
    width: 4096
    height: 4096
