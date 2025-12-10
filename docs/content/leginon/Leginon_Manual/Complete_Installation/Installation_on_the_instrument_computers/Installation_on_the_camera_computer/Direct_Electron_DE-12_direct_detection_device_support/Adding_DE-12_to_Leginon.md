## DE-12 is on a computer separated from the microscope

Please read [Using Leginon on a system where the microscope and camera are controlled by different computers](/leginon/Using_Leginon_on_a_system_where_the_microscope_and_camera_are_controlled_by_different_computers) first.

## Extra Package and Installation

  program/package                                         notes
  ------------------------------------------------------- -------------------------------
  DirectElectronAPI.exe                                   (Should come with the camera)
  [Google protobuf](http://code.google.com/p/protobuf/)   

> **Note:** See [portobuf installation instruction](/leginon/portobuf_installation_instruction)

## instruments.cfg

> **Note:** See [Instrument.cfg for DE-12](/leginon/Instrumentcfg_for_DE-12)
height and width should be set according to the model.

## orientation setup

Change the orientation in pyscope/de.py for frame orientation definition used in movie frame processing.

    # frame flipping configuration.
    # default here is for DE-12 orientation on FEI F20
    FRAME_LR_FLIP = True
    # frame rotate configuration. multiple of 90 degrees if needed
    # after the flip.  Direction + is x to -y.
    FRAME_ROTATE = 0

**Known values:**

DE-12 on Tecnai F20: FRAME_LR_FLIP = True, FRAME_ROTATE=0
DE-20 on Tecnai F20: FRAME_LR_FLIP = True, FRAME_ROTATE=--1

## Setup

-   Create the folder to store the dose fractionation raw frames. Default location is D:\frames.
-   Setup [raw frame file transfer](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Direct_Electron_DE-12_direct_detection_device_support/DDD_raw_frame_file_transfer) from a network data server.

## Testing

## Testing with pyscope


# start DE Server

# from python command line

from pyscope import de
c = de.DE12()
c.setExposuretime(407)
c.getImage()

- 407 ms is the 10 frame exposure time at 25.4 Hz default in DE-12

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


## Programs to open before Leginon Client: DE Server

See how to use DE camera usage in

-   [DE-12 introduction](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Direct_Electron_DE-12_direct_detection_device_support/DE-12_introduction) Please read this!!!
-   [Acquiring summed frame image thru Leginon](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Direct_Electron_DE-12_direct_detection_device_support/Acquiring_summed_frame_image_thru_Leginon)
-   [Triggering raw frame saving](/leginon/DDD_raw_frame_saving)
-   [Transferring raw frame images](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Direct_Electron_DE-12_direct_detection_device_support/DDD_raw_frame_file_transfer) off the solid-state drive of DE-12 during data collection to a network drive.
-   [Compiling corrected movie stack](/leginon/Make_DE-12_movie_stack) with Appion using bright and dark images acquired in Leginon
