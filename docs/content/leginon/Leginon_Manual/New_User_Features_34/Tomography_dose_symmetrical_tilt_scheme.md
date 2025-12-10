The dose-symmetric tilt series proposed by Wim Hagen et. al. https://doi.org/10.1016/j.jsb.2016.06.007 acquires first low angle tilts symmetrically in the plus and minus direction before collecting images are high tilt. The same tilt sequence was implemented in [3.3 release as "alternate" tilt series](/leginon/Leginon_Manual/Leginon_System_version_33/New_User_Features_33). Based on user feadback, we added "swing" option since it is reported at some sites that ti performs better due to the characteristics of the particular stage.

The difference of the tilt series is shown below:

"alternate": 0, --3, 3, 6, --6, --9, 9, 12,....
"swing": 0, --3, 3,--6, 6, --9, 9, --12,....

We also recommend users to investigate the effect of the following two options in pyscope/fei.cfg on the particular scope.

    # Stage with autoloader may need a constant preposition to have stable value
    DO_STAGE_ALPHA_BACKLASH = False
    # Alpha backlash delta (positive means preposition to negative direction) in degrees.
    STAGE_ALPHA_BACKLASH_ANGLE_DELTA = 3.0
