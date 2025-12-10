Most initial models establish nothing more than a preliminary sense of the overall shape of the biological specimen. In order to reveal structural information that can answer specific biological questions, the model requires refining. In single particle analysis, a refinement is an iterative procedure, which sequentially aligns the raw particles, assign to them appropriate spatial orientations (Euler angles) by comparing them against the a model, and then back-projects them into 3D space to form a new model. Effectively, a full refinement takes as input a raw particle stack and an initial model and is usually carried out until no further improvement of the structure can be observed, often measured by convergence to some resolution criterion.

## Refinement Options Available in Appion:

1.  [EMAN Refinement](/appion/Appion_Manual/Appion_User_Guide/Appion_Processing/Refine_Reconstruction/EMAN_Refinement)
2.  [Frealign Refinement](/appion/Appion_Manual/Appion_User_Guide/Appion_Processing/Refine_Reconstruction/Frealign_Refinement)
3.  [SPIDER Refinement](/appion/Appion_Manual/Appion_User_Guide/Appion_Processing/Refine_Reconstruction/SPIDER_Refinement)
4.  [IMAGIC Refinement](/appion/Appion_Manual/Appion_User_Guide/Appion_Processing/Refine_Reconstruction/IMAGIC_Refinement)
5.  [Refinement Post-processing Procedures](/appion/Appion_Manual/Appion_User_Guide/Appion_Processing/Refine_Reconstruction/Refinement_Post-processing_Procedures)

## Appion Sidebar Snapshot:

![](images/Picture_88.png)

## Notes, Comments, and Suggestions:

### Icosohedral conventions

When dealing with icosahedral particles such as viral capsids, particular attention should be given to properly orient the model (the icosahedral axes) to match specific conventions adopted by different softwares.

-   Models downloaded from ViperDB (http://viperdb.scripps.edu/) will always be orientated in the Viper convention with the icosahedral 2-fold axes aligned along the Cartesian x,y,z axes and when the positive z axis points toward the viewer:
    -   in the zx plan (2352): we first hit a 3-fold and then a 5-fold icosahedral axes
    -   in the zy plan (2532): we first hit a 5-fold and then a 3-fold icosahedral axes
         
-   Another frequently encountered icosahedral convention is the so-called Crowther convention in which the icosahedral 2-fold axes are aligned along the Cartesian x,y,z axes and when the positive z axis points toward the viewer:
    -   in the zx plan (2532): we first hit a 5-fold and then a 3-fold icosahedral axes
    -   in the zy plan (2352): we first hit a 3-fold and then a 5-fold icosahedral axes
         
        The Crowther orientation is related to the Viper one by a simple rotation of 90° along the z-axis and one can switch from Viper to Crowther using proc3d (EMAN) with the following command:
            proc3d model_Viper.mrc model_Crowther.mrc rot=0,0,90
-   A third convention may be termed EMAN convention as it is the one required by this package. It places an icosahedral 5-fold axis along the z axis, a 2-fold axis along y and a 3-fold axis close to x when looking down the z axis.

To convert a model from the Crowther orientation to the EMAN one, the following proc3d command is required:

    proc3d model_Crowther.mrc model_EMAN.mrc icos2fTo5f


Please note that a box can be checked when importing a model within appion to allow converting from Viper to EMAN orientation.

To assess visually in which orientation a model is, the simplest way is to do it in UCSF Chimera. After opening the map, press the Orient button in the Volume viewer to orient the z axis perpendicularly to the screen. Then open a file (named axis.bild for example) containing the following lines:

    .color red

    .cylinder  500.0  0.0  0.0  -500.0  0.0   0.0 1

    .color green

    .cylinder  0.0  500.0  0.0  0.0  -500.0   0.0 1

    .color blue

    .cylinder  0.0  0.0  500.0  0.0  0.0   -500.0 1”


This file will display the Cartesian axes x (red), y (green) and z (blue).

Below are the conventions used by the different softwares present within appion to generate and refine reconstructions (most allow to use different conventions).

-   **XMIPP**
    -   I1 (Viper convention)
    -   I2 or I (Crowther convention)
    -   I3: alternative 52 (as given by spider), 5fold axis in z and 2-fold in y. With the positive z-axis pointing at the viewer and without taken into account the 5-fold vertex in z, there is one of the front-most 5-fold vertices in -xz plane.
    -   I4 another 52 with the positive z-axis pointing at the viewer and without taken into account the 5-fold vertices in z, there is one of the front-most 5-fold vertices in +xz plane.
    -   I5 alternative 52 (used by EMBL-matfb).
         
-   **FREALIGN**
    -   I1 (Viper convention)
    -   I2 (Crowther convention)
         
-   **EMAN**
    -   Only uses the EMAN convention.

![](images/Picture_83.png)
![](images/Picture_81.png)

[Reconstruction Parameters](/appion/Reconstruction_Parameters)

[< Ab Initio Reconstruction](/appion/Appion_Manual/Appion_User_Guide/Appion_Processing/Ab_Initio_Reconstruction)|[Quality Assessment >](/appion/Appion_Manual/Appion_User_Guide/Appion_Processing/Common_Workflow/Quality_Assessment)
