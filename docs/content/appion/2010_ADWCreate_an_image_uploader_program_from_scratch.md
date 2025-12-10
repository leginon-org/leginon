## Problem statement:

We want to upload images, including defocal pairs into the database

-   four types of data collection: tomogram, tiltseries (RCT/OTR), defocal pairs, and normal
-   current version does tiltseries (maybe tomogram series) and normal, but not defocal pairs

## determine what the inputs are and what is required:

# folder with mrc images -- only support mrc files

# pixel size, specified in meters

# tiltseries/defocal information (# per set) -- cannot have both

    --images-per-tilt-series=3 --images-per-defocal-group=3

# two session modes, create new session or append to existing session
#* appending to a session is a dangerous things, so I am not going to support it.
#* single mode simplifies things dramatically

# input defocus and tilt angle:
#* optionally allow a batch file for individual defocus and angle information

    imagename <tab> defocus <tab> angle


#* have override commandline flags

    --angle-list=-45,0,45 --defocus-list=-2.0e-6,-4.0e-6,-6.0e-6


#* not required to allow future uploading from the web

1.  four data collection modes:
    #* **tomographic tilt series**: we cannot support uploading tomographic tilt series, pipeline requires Leginon information
    #* **RCT/OTR**: requires a tiltseries connection
    #* **defocal pairs**: require a AcquisitionImageTargetData connection, source:trunk/appion/appionlib/apDefocalPairs.py#L28
    #* **normal mode**: does not need any special treatment
2.  override session name???
3.  require a description

## Create the program file

-   Find the feature request in redmine or file a new one
-   Copy appionScript.py.template
-   Make executable
-   Commit to subversion

## Preliminary setup

-   Input options
-   Check conflicts

## Setup program to do the work

-   Create session
-   Obtain Scope/Camera information
-   Uploading to the database

## Test the program

## Create web interface
