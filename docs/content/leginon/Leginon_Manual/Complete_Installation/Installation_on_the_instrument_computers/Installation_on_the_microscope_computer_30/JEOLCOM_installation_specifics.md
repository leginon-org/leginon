These implementations have pyscope modules included in our repository

## JEOL 1400, 2100, 3100 and 3200 (and other scopes with JEOL's COM library)

Developed originally at Northwestern University by Christian Suloway

### Install 32-bit version of myami package on the associated camera computer

-   Instead of installing myami package on JEOL scope-controlling PC, the access to JEOLCOM usually work through the computer controlling the digital camera, regardless of the camera manufacturer.


-   In addition, probably because of the way JEOLCOM works, the installation is limited to 32-bit version.

### Alternatively, install myami package on JEOL scope-controlling microscope

-   This is only possible if this PC has TEMExternal3 installed and if it is on the same secured network as Leginon processing and database server.

See [JEOL External3 setup](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_microscope_computer_30/JEOLCOM_installation_specifics/JEOL_External3_setup)



------------------------------------------------------------------------

Program package web site local copy of win32 installer
comtypes 0.6.2 [http://sourceforge.net/projects/comtypes](http://sourceforge.net/projects/comtypes/files/comtypes/0.6.2/comtypes-0.6.2.win32.exe") comtypes-0.6.2.win32.exe
------------------------ ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -------------------------------------------------------------------------------------------------------------------------------------


Please check [Windows Installation All](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Windows_Installation_All) for important installation instruction regarding comtypes

## jeol.cfg

jeol.cfg records some instrument specific parameters that are required to convert the COM output to SI units that Leginon depends on as well as standard focus values needed for initializing defocus reference.

To do the pyscope communication test, copy pyscope/jeol.cfg.template to pyscope/jeol.cfg without any change.

## instruments.cfg

[scope]
class: jeolcom.Jeol
cs: 4.1e-3

## Testing with pyscope

In python command

    from pyscope import jeolcom
    t =jeolcom.Jeol()
    t.getMagnification()

You should get the current magnification at the microscope at the film camera position

## Leginon Calibration specifics

### Initial [Setup and Calibration for jeol.cfg](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_microscope_computer_30/JEOLCOM_installation_specifics/Setup_and_Calibration_for_jeolcfg)

### Follow the general installation and Leginon setup manual until you run "Calibrations" application and finishes obtaining your [Bright and Dark reference images](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Bright_and_Dark_reference_images).

### Refining scales in jeol.cfg

Unfortunately, Leginon's targeting relies on fairly good scale values in jeol.cfg. If you have low confidence on these initial estimate, we recommend doing some iterations of the following:

1.  Calibrate [pixel size](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Pixel_Size_Calibration) more accurately at each magnification used, including lower magnification with the defocus that will be used in experiment.
2.  Iterate adjustment of IMAGESHIFT_SCALE values in jeol.cfg and recalibrate in Leginon.
3.  Test the beam tilt scale using [get_beamtilt_scale.py](/leginon/Leginon_Manual/Instrument_Set-up/Calibrations_required_on_FEI_microscopes/TEM_Scripting_Beam_Tilt_Calibration)

### Image Beam Compensation calibration

JEM scopes do not have a high level function we can access through scripting to move image shift without affecting beam location. Therefore, any Leginon node that uses IMAGE SHIFT move type should be changed to BEAM-IMAGE SHIFT.

This affects calibration procedure in two ways:

-   Image Shift should be calibrated at smaller shift distance if the beam moves too much to affect correlation.
-   [Image Beam Compensation Calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Image_Beam_Compensation_Calibration) at mid and high mags (i.e. mags for hl and fa,fc,en,ef) is required to perform the compensation

## Custom Lens Programs

Note: This part requires microscopy knowledge. If you are a system admin, ask your local microscopist.

### sq preset magnification

For Leginon to function efficiently, it is highly desirable to have sq preset in Mag1 mode as the energizing/de-energizing of the objective lens is very slow. If the image acquired in standard Mag1 mode does not give large enough area to accommodate error in repeated targeting or covers too few holes, it may be a good idea to design and request a custom lens program that replaces an unused MAG1 magnification (typically the lowest one). For example, we have made such program replacing MAG1 1500x on JEM3200FSC @ NYSBC that gave us effective magnification of 750x. The lens program should be designed to energize objective lens and with balance of projection system to minimize distortion. Rotation of the image is o.k.

### lower intensity of the beam for very low magnification (such as gr) preset

For Gatan K2 camera installed on JEM microscope, the beam may to too intense at the low end of the magnification for grid atlas collection. While the camera is designed to protect itself when the beam is strong by retracting, it may not realize the problem when grid bar of the em grid reduces the average value. It is worth asking your local service engineer to make a lens program that has lower CL1 value. We replaced our spot 5 value with such a custom value.

## [Leginon Operation for JEM scopes](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_microscope_computer_30/JEOLCOM_installation_specifics/Leginon_Operation_for_JEM_scopes)
