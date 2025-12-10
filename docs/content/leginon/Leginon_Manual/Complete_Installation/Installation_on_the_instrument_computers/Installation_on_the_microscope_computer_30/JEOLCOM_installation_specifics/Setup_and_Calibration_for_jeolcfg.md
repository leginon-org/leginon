All setup and calibrations are done on the computer that has access to JEOL's External COM through temext.dll.

# Preparation

Decide roughly the magnification and defocus that will be used in Leginon presets. See [Pre-MSI Set-up](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Pre-MSI_Set-up) on preset design. This is necessary as the scale calibrated depends on the defocus when the latter becomes large.

## Copy from pyscope/jeol.cfg.template to pyscope/jeol.cfg

The current template is based on a JEM-3200FSC

## Modify [tem option] section in pyscope/jeol.cfg according to your scope

### BEAM VALVE

Not all scopes have beam or column valve. This specification makes sure jeolcom.py assumes column valve is always open.

### Using PLA for image shift

Image shift is normally achieved with IS1. However, PLA is a often a better choice as it does not induces beam tilt at
the specimen, although its range is more limited. When an omega filter is part of the scope, this also makes sure the beam not
affected at the entrance of the filter.

### CL3 RELAXATION MAG

The center of the beam on some scopes, such as JEM3200FSC at NYSBC, moves whenever CL3 is adjusted. In such as case, a more stable position can be reproduced if the beam intensity is cycled back and forth through cross-over through a programable procedure called "CL3 Relaxation", found in TEMCON/Option/Lens Relaxation if available. Leginon emulate that.

If you have this particular problem, set this option to a magnification where the procedure will be performed whenever the magnification is changed to a value larger than the "cl3 relaxation mag" value. Typically this is set at a value below the magnification for fa,fc, and final exposure so that these become more stable.
For example:

    CL3_RELAXATION_MAG = 2000

### LOWMAG NORMALIZATION MAG

When magnification is changed from mag1 mode to lowmag mode directly through jeolcom scripting, there is no normalization of projection lens applied. We often notice a distortion of image or changes in image shift in comparison to magnification change within lowmag mode. The LOWMAG_NORMALIZATION_MAG defines the mag Leginon will first go to when mode is changed to lowmag before applying the desired one. This has been different from scope to scope. Two good values that have had success in are (1)- The highest magnification that is in lowmag range that is registered in Leginon, and (2)- The magnification used for gr preset.

Note that not all lowmag mode magnifications are registered in Leginon. We do not include any magnification higher than the lower limit of mag1 magnifications.

### Lens Series within MAG1 and LOW MAG modes

There are distinct sets of objective and projection lens settings within MAG1 mode that gives
different scale and neutral values. We assign each of these lens series (LS) numbers, starting at 1 at
the lowest mags. Similarly, we also named the lowest LOWMAG mode lens series LM1 and assign a
different deflector scale to them.

The order of magnifications is therefore roughly

    LM1->the rest of LOWMAG->LS1->LS2->LS3->LS4->the rest of MAG1

-   To simply the mapping of magnification to the projection modes, MAG1 will be used if a magnification
    can be achieved by either LOWMAG and MAG1*

These four configurations like these therefore define the boundary of each lens series within the mode.

    LS1_MAG_MAX = 2500
    LS2_MAG_MAX = 4000
    LS3_MAG_MAX = 30000
    LS4_MAG_MAX = 100000
    LM1_MAG_MAX = 200

-   The boundary of these depends on Leginon presets magnification and defocus since the real magnification
    can deviate from the standard focus values, so do scale values. We found it is best to isolate those with very high
    defocus (sq and hl presets) from the others. In the above example, we effectively isolated every preset mag from others.

## Run pyscope/scalecalibrator.py to get values for different items in jeol.cfg

With the main viewing screen down do these at the computer with temext.dll registered.

1.  Double click pyscope/scalecalibrator.py to start it.
2.  The script will first make the scope go through all magnifications in LOWMAG and MAG1 range to determine valid magnifications.
3.  Enter the magnifications at which to calibrate. Make sure that you include at least one magnification in each lens series that you will use.
4.  Follow the instruction to shift each coil or mechanism by the amount indicated.

For example, for image shift with IS1, It says

    Preparie to calibrate IS1:
    Waiting for you to setup the initial condition


The initial condition means a visible feature at an easily remembered position such as the central dot on the main screen so that a shift can be recognized.
The distance between the major ticks of the linear scale bar on the main viewing screen corresponds to 1 cm at the film camera (i.e., nominal magnification)

After "hit a key to continue", this original IS1 value is recorded. You are then asked to

    Move IS1 by 1.0 cm on Main Screen in x direction


This means using x-axis IS1 knob to move the image feature by the amount. The major ticks of the scale bar on the main viewing screen corresponds to 1 cm at the film camera height.

The new IS1 value is saved when you hit a key to continue.

The output include

    [def]
    IMAGESHIFT_SCALE%LS2%X=8e-8

-   At the end of the calibration, it will ask for a filename to save the completed config. Save it in a name different from jeol.cfg, just in case you made mistakes.
-   Copy the good values to jeol.cfg and replace the old values there.

## modify jeol.cfg according to the scale output file

**Scale values will change with lens series, apparent magnification caused by large defocus if applied**

**We found that x and y coils do not always have the same scale**

**Missing calibration of unused lens series should not cause problem. There is no need to go through all of them just for the sake of completeness.**

**The scale does not need great accuracy at this point, a 20% error probably is not going to cause failure since there we will refine this later using Leginon calibration tools. See [Refine IMAGE SHIFT SCALE in jeol.cfg](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Image_Shift_matrix_calibration/Refine_IMAGE_SHIFT_SCALE_in_jeolcfg)**

## Record standard focus and neutral deflector values

Standard focus and neutral deflector values are the references for relative movements performed in Leginon. These values are stored in JEM scopes and will only change when engineer alignment is performed.

1.  Open pyscope/jeol.cfg with a text editor and leave it open so that you can enter values as you go.
2.  Double click pyscope/standard.py to start it.
3.  The script will first make the scope go through all magnifications in LOWMAG and MAG1 range to determine valid magnifications.
4.  Follow the instruction to go through each magnification that you will access.
5.  At the end the program will summarize the values which you can copy into jeol.cfg

**You may notice as I have that at LS2 (and probably above) the standard defocus is unchanged at different mags. In this case, put only the standard focus value for the lowest magnification so that the defocii can be modified together in this lens series**

## Set up stage backlash options

Backlash correction on JEOL scopes may be different individually. These options allows tuning of them.

There are two kinds of backlash correction. Full correction send the stage to a temporary position at a fix distance and direction relative to the final position first, before moving to the final. The temporary position used in "reduced correction" is at half the distance of the final movement. Its purpose is to save time.

BACKLASH_SCALE: This has separated X, Y values. They defines the size of backlash correction (in meters) the stage makes when full correction is performed. To determine the proper value, observe the movement of the stage when you use TEMCON program "Operation/Specimen Position" to recall a position from memory.

BACKLASH_LIMIT%FULL: The smallest movement in meters at which a full correction will be performed. TEMCON program does this at all distance, but it is time consuming. We switch to reduced method at 10 um, i.e. BACKLASH_LIMIT%FULL = 1e-5

BACKLASH_LIMIT%REDUCED: The smallest movement in meters at which a reduced correction will be performed. We currently use reduced method down to at 0.5 um, i.e. BACKLASH_LIMIT%FULL = 5e-7

## Enter STAGE_LIMIT and ACCURACY of the stage movement

axises are X,Y,Z,A, and B. XYZ are in meters, AB are in radians

Stage movement becomes random once it is below a particular value. This is scope dependent. You can specify a different values if different from the default. Please adjust the [Iterative Stage Movement](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Iterative_Stage_Movement) Tolerance accordingly. [Reproducibility test](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Iterative_Stage_Movement/Determine_Target_Tolerance_and_Acceptable_Tolerance) can be done in Navigation Node.

Jeol stage XY accuracy from our experience is in the range of 0.1-0.2 um.

Accuracy in A (TX) can be estimated by looking at the fluctuation in value displayed in JEOL TEMCOM. It is around 0.2 degrees in the two cases we have.

## Examples

jeol.cfg.template is a real jeol.cfg used on NYSBC JEM3200FSC equipped with DE-20. The effective pixel size is 1.4 um at 62000 x nominal mag. It has energy filter and automated aperture but we do not yet align the slit during the experiment. The automated apertures are also deactivated since its main use in removing/inserting objective aperture is not precise enough for our purpose. We also have a special lens program for 2000x which gives effective mag of 750x used for DE-20 sq mag. Because of that it belongs to its own sub-lens series. [j3200 de20 preset design](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_microscope_computer_30/JEOLCOM_installation_specifics/Setup_and_Calibration_for_jeolcfg/J3200_de20_preset_design)

Attached is jeol.cfg used on NYSBC JEM2100F. Gatan K2 Camera is used here with effective pixel size of 1.4 Angstrom at 25000 x nominal mag [j2100f k2 preset design](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_microscope_computer_30/JEOLCOM_installation_specifics/Setup_and_Calibration_for_jeolcfg/J2100f_k2_preset_design)
