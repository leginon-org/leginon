Most calibration and operation are similar to that of a typical digital camera.

Leginon treats linear/counted/super-resolution modes of K2 Summit as three cameras. Therefore, each needs its own calibrations.

## Super-resolution calibrations

Super resolution mode is especially hard to calibrate due to its image size. Instead of going through the actual calibration, it is easier just copying from counting mode.

There is a script in your myami download under dbschema. Just add option 1 at the end. You may also download it from the repository

http://emg.nysbc.org/redmine/projects/leginon/repository/changes/dbschema/tools/copy_k2_super_cal.py?rev=trunk

1. If you have not saved a preset GatanK2Super, do so. It will register the camera in the database.

2. Run a test first. Make sure it does not give errors.

    python copy_k2_super_cal.py hostname high_tension

3. Add commit flag 1 when rerun to commit the change, for example,

    python copy_k2_super_cal.py hostname 200000 1
