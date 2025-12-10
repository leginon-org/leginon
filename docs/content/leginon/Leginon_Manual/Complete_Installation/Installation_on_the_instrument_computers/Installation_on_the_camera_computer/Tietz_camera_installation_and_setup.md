## Many Tietz cameras are controlled by a computer separated from the microscope

Please read [Using Leginon on a system where the microscope and camera are controlled by different computers](/leginon/Using_Leginon_on_a_system_where_the_microscope_and_camera_are_controlled_by_different_computers) first.

## Extra Package and Installation

  package                                                     local win32 installer
  ----------------------------------------------------------- -------------------------------------------------------------------------------------------------------
  Python for Windows extension (pywin32) for 32-bit machine   pywin32-218.win32-py2.7.exe
  Python for Windows extension (pywin32) for 64-bit machine   pywin32-218.win-amd64-py2.7.exe

**double click the windows installer to start**

  program/package   notes
  ----------------- -------------------------------
  CAMC4.exe         (Should come with the camera)

## Register CAMC4.exe

-   From the command prompt, run the following commands.
        CAMC4.exe /regserver

## Run updatecom.py

-   From a command line window:
        cd C:\python27\Lib\site-packages\pyscope
        C:\python27\python.exe updatecom.py


-   The output sould contain this output
        initializing Tietz CCD Camera
        Found: CAMC4 1.0 Type Library
        done.

You can ignore error messages regarding other com modules.

## Register the Tietz ping callback function

-   From a command line window:
        cd C:\python27\Lib\site-packages\pyscope
        C:\python27\python.exe tietzping.py

## check camc.ini


CAMC4 has its own configuration file "CAMC.ini" that will normally be set up already, but you can search for it on your computer and confirm that everything looks right. It will have configuration parameters for several cameras and only one of them will be activated. The only parameter that may need some adjustment is the readout geometry, which affects the rotation and mirror of the image.


## instruments.cfg

This is extracted from pyscope/instruments.cfg.template

    ## Tietz/TVIPS Camera using various drivers.  Chose only the driver
    ## that works with your camera.  Optionally, you may also select
    ## the Simulation camera.  A test script is available to help you figure
    ## out which ones are available to you.  Run the script:  tietztest.py
    ##   - tietz.TietzSCX
    ##   - tietz.TietzPXL
    ##   - tietz.TietzPVCam
    ##   - tietz.TietzFC415
    ##   - tietz.TietzFC416
    ##   - tietz.TietzFC816
    ##   - tietz.TietzFastScan
    ##   - tietz.TietzSimulation

For example, instruments.cfg for F416 looks like this:

    [Tietz Camera]
    class: tietz.TietzF416
    zplane: 5
    height: 4096
    width: 4096

-   I use zplane of 5 because this is a bottom-mount camera that does not retract. Therefore it is always the lowest.

## Setup

-   Set camera configuration to give the [standard Leginon orientation](/leginon/Leginon_Manual/Instrument_Set-up/Leginon_image_orientation).

## Testing with pyscope

**F416 camera is used in this case**

1. Close TVIPS TCL/EMMENU
2. From python command shell or IDLE:

    from pyscope import tietz
    t = tietz.TietzF416()
    t.getImage()


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


## Trouble shooting


When Leginon initializes the camera, a program called CAMC4 should start automatically in the backgound. This is confirmed by the little camera icon showing up in the system tray in the lower right of the screen. Also, task manager can be started to confirm CAMC4 is running. Sometimes problems occur if more than one CAMC4 is running at the same time, so task manager will help identify this.

If Leginon is not initializing the camera or not getting proper images, you should first test image acquisition using TVIPS software to make sure it is not a hardware issue. Use TCL or there is a test program called TestMFCCamera that can acquire an image and test the CAMC4 operation.


## Programs to open before Leginon Client: None. TCL/EMMENU must be closed
