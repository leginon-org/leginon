## (Version 3.0) Change Flag in pyscope/dmsem.py if you have DM 2.30 version and requires flip/rotation to give the Leginon orientation.

In standard python site-package installation, this file is at C:\Python27\Lib\site-packages\pyscope\dmsem.py

Find this line near the top:

    isDM230 = False


Change it to

    isDM230 = True

## (Version 3.1) Define local configuration

## In C:\Python27\Lib\site-packages\pyscope/dmsem.py

    # DM Version
    DM_VERSION = '2.30.542.0'
    # the value in DM camera config
    K2_CONFIG_FLIP = True
    # multiple of 90 degrees (i.e. put 1 if 90 degrees, 3 if 270 degrees)
    K2_CONFIG_ROTATE = 3
    # raw frame base directory. Use '\' as path separator
    RAW_FRAME_DIR = 'D:\frames\'

1. Find DM_Version in DM gui under its menu bar : /Help/About DigitalMicrograph
2. Fill in K2_CONFIG_FLIP and K2_CONFIG_ROTATE according to DM gui under its menu bar: /Camera/Configure Camera. The comment line above the value setting explains the meaning of the value.
3. Enter the drive the directory where raw frames will be saved.
