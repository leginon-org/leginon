This note is specific instruction for those who have been using the K2 summit camera implementation in svn trunk for the update required to go from before r17514 to after r17561.

## instruments.cfg

The python module used by Leginon in pyscope has changed from gatank2.py to dmsem.py (stands for Digital Micrograph Serial EM). Therefore, instruments.cfg on the k2 computer needs to be modified.

    [Gatan K2 Linear]
    class: dmsem.GatanK2Linear
    zplane: 50
    width: 3710
    height: 3838

    [Gatan K2 Counting]
    class: dmsem.GatanK2Counting
    zplane: 50
    width: 3710
    height: 3838

    [Gatan K2 Super]
    class: dmsem.GatanK2Super
    zplane: 50
    width: 7420
    height: 7676

## control of frame exposure time in Leginon gui

The frame exposure time for dose fractionation is now changable from Leginon camera gui. 200 ms is a reasonable number for ~ 1 Angstrom/pixel images. Because of this feature, please check and perform database schema update. The update only affects DD camera data that has frame-saving ability.
> **Note:** See external reference `Appion:Run Database Update Script`

## raw frame saving location and format change

The frames are now saved as mrc image stack not single files in a folder.

The file location after rawtransfer.py is run is now all in a folder parallel to leginon data so that it is easier to remove and backup with different rules.
For example, if leginon data image path is /your_mount_point/leginon/your_session/rawdata, then rawtransfer.py will move the rawdata to /your_mount_point/frames/your_session/rawdata.

## other changes that you will notice:

1.  The valid camera geometry is now listed, customized for each camera model. This is a very large for counted and linear mode of K2 but is very small in super-resolution mode since it makes no sense to bin super-resolution images.
2.  The problem of occasional frame rate override is fixed.
