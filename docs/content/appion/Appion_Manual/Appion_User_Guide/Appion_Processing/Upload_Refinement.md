## How to upload a refinement that has been carried out in an external package, i.e. outside of Appion

# create a directory tree in the "recon" folder titled "Your_Refinement_Procedure/external_refinement_results", as for example: /ami/data17/appion/11jan11a/recon/external_package_test/external_package_results

# all files described below must reside in the "external_refinement_results" directory, otherwise the upload will not work.

# define a timestamp, e.g. "11jun03a" or "my_favorite_refinement_procedure_june03" or whatever you want.

# **AT LEAST 2 files are needed per iteration per reference number** for the refinement (the latter being the number of output models / references produced)

## 3D mrc file titled "recon_'timestamp'_it#_vol#.mrc (it# and vol# have 3 integers), as for example "recon_11jul18z_it001_vol001.mrc"

## particle data file titled "particle_data_'timestamp'_it#_vol#.txt" (it# and vol# have 3 integers), as for example "particle_data_11jul18z_it001_vol001.txt". An [example file](http://emg.nysbc.org/redmine/attachments/963/particle_data_11jul18z_it001_vol001.txt) is attached. This file **MUST** contain the following columns:

### particle number - **!!! PARTICLE NUMBERING STARTS WITH 1 !!!**

### phi Euler angle - rotation Euler angle around Z, in degrees

### theta Euler angle - rotation Euler angle around new Y, in degrees

### omega Euler angle - rotation Euler angle around new Z (in-plane rotation), in degrees

### shiftx - in pixels

### shifty - in pixels

### mirror - specify 1 if particle is mirrored, 0 otherwise. If mirrors are NOT handled in the package, and are represented by different Euler angles, leave as 0

### 3D reference # - 1, 2, 3, etc. Use 1 for single-model refinement case

### 2D class # - the number of the class to which the particle belongs. Leave as 0 if these are not defined

### quality factor - leave as 0 if not defined

### kept particle - specifies whether or not the particle was discarded during the reconstruction routine. If it was KEPT, specify 1, if it was DISCARDED, specify 0. If all particles are kept, all should have a 1.

### post Refine kept particle (optional) - in most cases just leave as 1 for all particles

# the optional additional files are:

## An [FSC file](http://emg.nysbc.org/redmine/attachments/964/recon_11jul18z_it001_vol001.fsc) titled "recon_'timestamp'_it#_vol#.fsc (it# and vol# have 3 integers), as for example "recon_11jul18z_it001_vol001.fsc" Lines that are not read should begin with a "#". Otherwise, the first column must have values in inverse pixels. The second column must have the Fourier shell correlation for that spatial frequency. You can have as many additional columns as you would like, but they will be skipped.

## .img/.hed files describing projections from the model and class averages belonging to those Euler angles. The suggested format is as follows: image 1 - projection 1, image 2 - class average 1, image 3 - projection 2, image 4 - class average 2, etc., but you can have any format you like. see below ![](images/projections_and_averages.png)

# run the command uploadExternalRefine.py, specifying, at a minimum, the following options:

-   ---rundir= (full path to the results NOT INCLUDING the directory "external_refinement_results", e.g. ---rundir=/ami/data17/appion/11jan11a/recon/external_package_test)
-   ---runname= (the tail directory of the rundir, e.g. ---runname=external_package_test)
-   ---description= (whatever you want)
-   ---projectid= (from the database)
-   ---expId= (from the database)
-   ---stackid= (from the database)
-   ---modelid= (from the database)
-   ---uploadIterations= (e.g., 1,2,3,4,5)
-   ---apix= (pixelsize, in Angstroms)
-   ---box= (boxsize, in pixels)
-   ---numberOfReferences= (number of output models / references)
-   ---numiter= (number of successful iterations run)
-   ---symid= (from the database, can put 25 for C1 symmetry)
-   ---timestamp= (see above)
-   ---commit (commit results to the database, use ---no-commit if testing)

An example command is:

**uploadExternalRefine.py ---rundir=/ami/data17/appion/11jan11a/recon/external_package_test ---runname=external_package_test ---description="testing out external upload on 11jan11 data, emanrecon11, first iteration" ---projectid=224 ---no-commit ---expId=8397 ---uploadIterations=1,2,3,4,5 ---stackid=127 ---modelid=19 ---mass=3800 ---apix=2.74 ---box=160 ---numberOfReferences=1 ---numiter=1 ---timestamp=11jul18z ---symid=25**
