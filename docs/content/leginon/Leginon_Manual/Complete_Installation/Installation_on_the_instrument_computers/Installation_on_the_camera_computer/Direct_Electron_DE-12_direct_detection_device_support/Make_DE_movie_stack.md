We've made appion function to correct raw frames from DE12 or DE20 collected through Leginon.

Two simple examples that uses the module are attached here.

**correctframes.py** let you correct a range of raw frames in an image and output as mrc file.
**correctstack.py** let you correct each frame in the specified summed image and output at 2D image stack in mrc format.

type:

    python correctframes.py


for the options

In Appion, you should get a processing menu for Direct Detector Tools
That will allow you to choose what images to correct in the usual Appion way and make the mrc stacks for the whole session on given preset.

## How to do it yourself

### Find the reference images

Use leginon/getReferences.py to find the reference images for the leginon sum image.

### You can convert the tiff frame file to single mrc file with pyami/tifffile.py and pyami/mrc.py

This is written by The Regents of the University of California and Produced by the Laboratory for Fluorescence Dynamic.

To convert to numpy array, you can use these lines

        from pyami import tifffile
        tif = tifffile.TIFFfile(frameimage_path)
        a = tif.asarray()

To write a numpy array to mrc file

        from pyami import mrc
        mrc.write(a,framemrc_path)

### DE dark reference intensity comes from dark current and is proportional to exposure time. To do dark correction, you need to know the frame rate (typically 25 frames per second) and scale the dark image which is made to be 1 second.

Therefore the corrected frame at 25 frames per second need to be corrected in the following way:

    corrected_frame = (raw_frame - dark/25) * norm

### Beware of image flip/rotation.
