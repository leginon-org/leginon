To save eer format on Falcon4, you need to modify fei.cfg on your scope computer. Set these under [camera] section following the template in pyscope/fei.cfg.template

    # Falcon EC EER
    SAVE_EER = True
    # Falcon EC Gain reference directory for EER files
    EER_GAIN_REFERENCE_DIR = z:\ImagesForProcessing\BM-Falcon\300kV
    # Falcon EER render factor. Some version of TFS software works with Falcon 4 is 7, Falcon 4i is 9, the newer versions should be 1
    EER_RENDER = 1
    # Falcon EER may flip relative to mrc
    EER_FRAME_FLIP = False
    # Falcon EER may rotate relative to mrc after flip.
    #   1 rotates features on x to -y axis direction
    EER_FRAME_ROTATE = 0

## SAVE_EER

This allows you to turn eer saving on and off.

## EER_RENDER

EER format movie should record as rolling shutter frame rate. In leginon, this is saved under camera meta data as nframes. Depending on version of TFS software and camera model, this is either 1, 7, 9. See comment above. nframes for 1 second exposure should give ~240 nframes. If this is 7 times larger on your camera, change this to 7 if it is Falcon 4. Getting this wrong affects motioncor2 settings in Appion.

## EER_GAIN_REFERENCE_DIR

## EER_GAIN_REFERENCE_DIR is where leginon will import gain reference collected in TFS Falcon software. This reference is needed only for EER format, not mrc format.
