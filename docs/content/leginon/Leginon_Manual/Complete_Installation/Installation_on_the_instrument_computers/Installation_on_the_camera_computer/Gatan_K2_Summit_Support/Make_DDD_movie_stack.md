## Make DDD movie stack

The following section comes from Appion Manual

> **Note:** See external reference `appion:Direct_Detector_Frame_Processing`

## Making Gain/Dark correction one image at a time without saving results to databases

Two scripts are attached here. They use Leginon infrastructure to locate references and do gain/dark correction and bad pixel/column/row correction. It, however, does not involve saving results to the leginon/appion databases. These are good for testing of add your own idea to it.

**correctframes.py** let you correct a range of raw frames in an image and output as mrc file.
**correctstack.py** let you correct each frame in the specified summed image and output at 2D image stack in mrc format.

type:

    python correctframes.py


for the options

> **Note:** See [Make movie stack with dark/bright/norm/gain references yourself without Leginon/Appion libraries](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Gatan_K2_Summit_Support/Make_DDD_movie_stack/Make_movie_stack_with_darkbrightnormgain_references_yourself_without_LeginonAppion_libraries)
