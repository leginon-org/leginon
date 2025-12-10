## reconstruct an ab initio model using common lines

1.  select a set of ~20 good class averages in the image viewer, and upload them as a template stack (call it, e.g. "ts_initial_models")
2.  select as many of the class averages that have reliable features which you think are real and correspond to the Fab-bound complex (could be 50, could be 100, etc ...), and upload that as another template stack (call it, e.g. "ts_refinement")
3.  You can access the common lines method under the menu "ab initio reconstruction" and "automated common lines" in Appion. Go there.
4.  Under "iterative model creation" select the first template stack, "ts_initial_models"
5.  Under "refinement of aligned and clustered model" select the second template stack, "ts_refinement"
6.  keep all parameters as default, and try EMAN for iterative model creation. Then fill out the number of images per volume. This should be ~50% of the number of images in the "ts_2g12_initial_models" stack. If you have, e.g. 30 images, this value should be ~15. You can also try IMAGIC for iterative model creation by switching between the two options.
7.  Fill out the bottom radii for the particles and give a mass. For example, for 2g12, these should probably be: "radius of mask"=200 ; "inner alignment radius" = 0 ; "outer alignment radius" = 140 ; "particle mass" = 750
8.  Launch the job
9.  repeat 1-8 with an identical job, EXCEPT that uncheck "iteratively align class averages to each other", and give the run a different name (for example, you can have two runs, titled "acl1" and "acl1_noiteralign" ...).

## refine the reconstructed model using symmetry

Common lines determination can potentially be difficult for symmetric particles, because when the reconstructed volume contains errors, determination of the symmetry axis by automated means is difficult. For this reason, the automated common lines operation inside Appion does not employ symmetry. After the construction of an initial model, it is often useful to (1) determine the symmetry axis either automatically or manually and (2) further refine the model against a group of well-resolved class averages.

1.  align the C1-reconstructed model to its symmetry axis. You can do this in one of several ways. (a) `proc3d input.mrc output.mrc rot=<alt,az,phi>`, but you have to know the specific Euler angles (alt, az, and phi) by which to rotate the model to get it to the specific orientation. You can approximate the Euler angles by using v4, e.g. `v4 input.mrc` and then adjusting the angles accordingly. (b) align the model to a previously determined trimer in Chimera, then resample on the grid. for example, given that volume #0 is the symmetrized trimer, and volume #1 is the C1-reconstruction, after alinging and fitting volume #0, enter the command `vop resample #1 onGrid #0` and save the resampled mrc file. It should be on the appropriate symmetry axis.
2.  log into guppy and enter into an interactive session: `qsub -I -l nodes=1:ppn=8`
3.  currently, you have to source my .bashrc or .cshrc (depending on which shell you're using):
    -   source /home/dlyumkis/common_lines_scripts/SET_ENVIRONMENT.bashrc
        OR
    -   source /home/dlyumkis/common_lines_scripts/SET_ENVIRONMENT.cshrc
4.  refine the volume
    -   refine_volume.py -h (this will give you a list of options for the script)
5.  the important options are ---symmetry, ---outer_radius, ---mask_radius (the latter two expressed in Angstroms)
    ... for example ...
    -   refine_volume.py ---volume=input.mrc ---images=/path/to/images.hed ---symmetry=c3 ---outer_radius=140 ---mask_radius=200 ---nproc=8 ---apix=4.84
        ... where your input.mrc is the aligned volume and the images.hed is a set of **class averages** (as many as have good, distinguishable features, e.g. 50,100,200, etc.)

[< Random-Conical Tilt (RCT) Reconstruction workflow](/appion/Appion_Manual/Appion_User_Guide/Appion_Processing/Common_Workflow/Random-Conical_Tilt_RCT_Reconstruction_workflow) | [Processing Cluster Login >](/appion/Appion_Manual/Appion_User_Guide/Appion_Processing/Processing_Cluster_Login)
