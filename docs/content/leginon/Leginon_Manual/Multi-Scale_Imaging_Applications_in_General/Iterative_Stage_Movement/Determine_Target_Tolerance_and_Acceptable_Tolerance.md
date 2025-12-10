In [Iterative Stage Movement](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Iterative_Stage_Movement), Target Tolerance is the goal of targeting error, while Acceptable Tolerance is the fall-back cut-off. The values used depends on the purpose and the performance of the compustage on the microscope.

## Target Tolerance

At some small distance, the motor on the compustage can no longer drive the stage predictably. Target Tolerance should be chosen above this value. Use "Test Stage Reproducibility" tool in Navigation Node to estimate this value.

Presets Manager> send the preset where the movement will be performed, normally at "hl" preset.
Navigation> left click on "Test Stage Reproducibility" tool icon ![](images/ruler.png) to open dialogue.
Navigation/Test Stage Reproducibility> Leave Angle field empty to move from random direction in the test.
Navigation/Test Stage Reproducibility> Enter number of measurement in "Move:", typically 5-10
Navigation/Test Stage Reproducibility> Enter distance to move. Change this value each run until you find out when it starts to fail frequently.
Navigation/Test Stage Reproducibility> Click "Run" to start test

In addition, because the iteration of stage movement takes time and have to expose the specimen, we recommend using as loose a tolerance that will allow the movement to succeed in two to three tries. Observe the movement during usage is the best way to determine the proper value.

### Acceptable Tolerance

Obviously, Acceptable Tolerance should be larger than Target Tolerance. The tighter this tolerance is, the more the targeting will fail, and resulting much waste of time. Apart from that, it depends on the purpose.

-   For moving roughly to the center of the hole to minimize image shift required in the multiple final exposure, a tolerance of 1/3 of the hole diameter is sufficient.
-   For tomography or RCT targeting, the tolerance should be set to much less than half the length of the "tomo" or "en" preset, respectively.
