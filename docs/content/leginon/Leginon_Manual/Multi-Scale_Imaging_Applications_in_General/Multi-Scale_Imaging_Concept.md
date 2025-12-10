Multi-Scale Imaging (MSI) is the back-bone of many Leginon applications. The setup and
calibrations required for an imaging sequence can be understood better when it is compared to
a low dose mode on a typical electron microscope such as FEI Tecnai.

## Low Dose Kit

A typical low dose kit contains three modes: Exposure, Focus, and Search

-   Exposure Mode for final image acquisition: The image shift at (0, 0) and beam shift
    to center on the detector. The beam intensity, diameter, and the detector exposure time
    are matched to provide optimal low-dose exposure that does not irradiate other
    area.


-   Focus Mode for focusing the microscope to the height of the specimen at an area
    other than that of the final exposure: The image shift is set to non-zeros. The beam
    shift is compensated so that the beam is centered on the detector. As a result, the
    image of a remote area is imaged on the detector. For example, FEI Tecnai's Focus mode
    allows the user to set S1 and S2 focus location by defining the radius of the offset and
    an angle of rotation for S1 with S2 always 180 degree opposite to S1. The origin of the
    image offset is at (0,0). Since focusing is normally done at a magnification equal to or
    higher than Exposure, there is only a very small magnification dependent image
    shift.


-   Search Mode for searching for and centering a potential target. The Search mode is
    usually set at a low magnification for large field of view and minimal dose. In
    operation, the user looks at an image in the viewing screen, finds a potential target
    object, and then moves the specimen stage with the goniometer to locate a potential
    target by moving it to the center of the viewing screen, which is also the center of the
    detector. If aligned properly, this will also be the center of the image taken at the
    Exposure mode.

![](images/lowdose.png)

This figure shows the steps of targeting an object for low dose image collection.
First, move the object (gray star) to the center of the viewing screen in Search Mode
(yellow circle). If properly aligned, then Focus at the set offset radius and angles,
and at last acquire final image at the center in Exposure mode (Red square).

Because of the large difference in magnification, it is often necessary to adjust
the image shift of the Search Mode to achieve proper alignment to Exposure mode.

## Setup of the low-dose kit

Although not obvious to everyone, the low dose kit does require set up. These
include:

-   Set the magnification, spot size etc. desired for each mode.


-   Align image shift of the Search mode to the Exposure mode so that object at the
    center of the viewing screen is at the center of the Exposure image.


-   Adjust the radius and angle of the two Focus location to optimize their image
    shift relative to that of the Exposure mode.


-   Align the beam for each modes to the optical (detector) axis.


-   Adjust the intensity of the beam for proper exposure in each mode.

![](images/bad_align_lowdose.png)

This figure illustrates the consequence of misalignment of image shift of the lower
magnification Search Mode to the Exposure Mode. The yellow circle represents the field of
the view in the search mode, the gray star an object that the user centers as a target for
final exposure (red square). When the image shift in the Search mode is not aligned to the
exposure, the object centered in the field of the view in Search mode is not centered in
the Exposure mode image. Note that in this case, the image shift offset origin of the two
Focus modes (black) is such that it is aligned with Exposure mode.

## Leginon MSI analog of the Low Dose kit

Leginon separates the function of the low dose kit idea into three parts: defining the
presets, choosing Acquisition/Focus targets, and moving to a target on an image.

### Low-Dose-Kit Equivalent Presets

The presets in Leginon can be set up like the three modes in the low dose kit with two
exceptions: First, there is only one Focus preset, and second, the focus preset has the
same image shift as the Exposure preset.

Low-Dose-Kit equivalent preset parameters:

  Magnification (example):   Preset name:   Image Shift (x,y):
  -------------------------- -------------- --------------------
  550                        Search         Aligned
  100000                     Focus          0,0*
  50000                      Exposure       0,0

*Focus Preset is also at image shift (0,0) since the target selected for it is
separated from that for Exposure Preset.

### Acquisition and Focus Targets

Leginon users can select more than one type of targets on a single image. For a
low-dose-kit analog, we can define one or many Acquisition targets (used for acquiring
images at Exposure Preset) on an image acquired in the Search Preset. In addition, we
define one Focus target on the same image (for focusing at Focus Preset, of
course).

Because the focus targets can be selected independently from the those for the final
exposure, the image shift for the Focus preset is (0,0) rather than microns away from the
origin. At its current state, Leginon only focus at one position per low mag Search
image.

### Moving to the Targets

When a person operates in low-dose mode, he/she finds a target on the image in the
viewing screen and move the stage according to its relative position to the viewing screen
to reach the target, i.e., center the target on the screen in Search mode. Leginon moves
to the targets using a similar logic. When a target is selected from an image acquired
using the Search Preset in Leginon, in order to acquire a new image in Focus or Exposure
mode at this target, the program move the target relative to the center of the CCD
detector using the knowledge (i.e., calibrations) of the Search Preset at which the old
image is acquired, not that of the Focus or Exposure Preset with which the new image will
be acquired.

![](images/MSI_lowdose.png)

This four paneled figure shows how Leginon performs a low-dose kit type of image acquisition
sequence where the focus target (blue) is first moved to the center of the CCD and then
the exposure target(green). Compare this with the one on [low dose
kit](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Multi-Scale_Imaging_Concept#Setup-of-the-low-dose-kit).

As a consequence, let's say that we decide to move to the target by moving the stage,
we will want the Exposure node to use the following settings: Preset-Exposure; Move
Type-Stage. However, the required stage position matrix calibration is at that of the
Search Preset.

### Setup of the Presets in a low-dose equivalent MSI

Set up of the presets is therefore not very different from that for the low dose
kit.

* Set up magnification, spot size, beam intensity for each preset.

* Set the image shift (0,0) for Focus and Exposure preset.

* Align the image shift of Search preset to that of Exposure/Focus.

* Align the beam shift for each mode to the optical/detector axis.

### Calibrations required

For the above imaging sequence, the calibration requirements with manual focusing and
target selection are

* Pixel size calibration for 550x, 50,000x, and 100,000x

* Bright/Dark reference images for the CCD configuration used for each
preset.

* Image shift matrix calibration for 550x to perform image shift alignment of Search
Preset in Leginon.

* Stage position matrix calibration for 550x to move the target selected.

[Ways of Moving to Targets in Nodes that acquire images inside MSI >](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Ways_of_Moving_to_Targets_in_Nodes_that_acquire_images_inside_MSI)
