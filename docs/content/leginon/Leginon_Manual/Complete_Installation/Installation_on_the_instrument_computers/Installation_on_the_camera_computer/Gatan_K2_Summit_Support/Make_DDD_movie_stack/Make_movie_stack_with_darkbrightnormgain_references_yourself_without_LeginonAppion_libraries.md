## Make movie stack with dark/bright/norm/gain references yourself without Leginon/Appion libraries

If you want to do everything yourself, you can use the python script

[getReferences.py](http://emg.nysbc.org/redmine/projects/leginon/repository/changes/branches/myami-3.1/leginon/getReferences.py)

to find the location and filenames of the bright, dark, norm (also known as gain) references and work on them yourself. The filenames are formatted to include various information. For example,

**14aug12a_12221419_00_512x512_norm_0.mrc** is a norm reference image at dimension of 512x512. It was calculated from the dark and bright images shown by the script and was taken during session 14aug12a at 22:14:19 and is for correction channel 0.

You will also find reference images from correction channel 1 in the same folder with name like **14aug12a_12221421_00_512x512_norm_1.mrc** which you may either ignore or use it in one of the two ways:
1. Create an average image with the one from correction channel 0 to get a reference image with better statistics ( i.e., 2n sampling of the population rather than n ).
2. Alternate its usage with the channel 0 result if your custom alignment program compares individual frames against each other, similar to the way Leginon use it for improving correlation peak with week signal.

**Beware that the fames are often in different orientation from the reference images in Leginon**

## Leginon/Appion 3.2 and up

For Leginon 3.2 and up, a **references** folder is created in the folder containing the raw frames. Inside the folder are
| file | contents |
| reference_list.txt | gain/dark/defect/rotation/flip information for each frame stack |
| *norm_0.mrc | gain references as used in Leginon orientation |
| *dark_0.mrc | dark references as used in Leginon orientation before scaling to frame time |
| *norm_0_mod.mrc | gain references modified according to flip and rotation specified in reference_list.txt so that it can be applied directly to single frame |
| *dark_0_mod.mrc | dark references modified according to flip, rotation, and frame time specified in reference_list.txt so that it can be applied directly to single frame |
| defect_plan*.txt | defect rows, columns, pixels, respectively |
| defect_plan*_mod.txt | defect rows, columns, pixels, respectively, after flip/rotation modification to work with the frames |

## How to do the correction:

To apply the gain/dark correction, you need to use the equations found in [Corrector](/leginon/Leginon_Manual/Node_Descriptions/Corrector)

If there are no bad pixel/column/row on your camera that you included in your correction plan, you can feed the properly rotated/flipped references (*_mod.mrc) to the 2.0+ version of the drift correction program (motioncorr) by Xueming Li.

**simple_correctstack.py** can do the same as well using the library of Leginon/Appion, but not the database.

To apply defect correction, you will have to write an algorithm similar to what is in leginon correctorclient.py to find a good pixel not in the plan but closest to the defect as a substitution for the defected value.
