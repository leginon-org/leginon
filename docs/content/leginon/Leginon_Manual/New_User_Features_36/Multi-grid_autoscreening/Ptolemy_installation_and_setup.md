Automated square and hole finders are added to leginon to use Ptolemy (https://arxiv.org/abs/2112.01534) to determine optimal targets using computer vision algorithm and Convolutional Neural Network trained on user target selections accumulated at Simons Electron Microscopy Center at New York Biology Center (SEMC@NYSBC).

Not (Jan 2023): Ptolemy development has moved on without a release branch. If you want the version that is working and compatible with Leginon 3.6, Please checkout at the commit
SHA

f9105de58330bbb2abb4525a242be0e62340c59e

This implementation requires Ptolemy which has a separate license. For this release, the communication is through command line interface and rely on shared file system.

-   At SEMC@NYSBC, Ptolemy, which was tested on python 3.9, runs in anaconda environment on the same CentOS7 computer where the main leginon process is.

## Install Ptolemy and setup shell scripts to use its cli for [grid square finding](/leginon/Leginon_Manual/New_User_Features_36/Multi-grid_autoscreening/First-time_autoscreening_setup/Setup_Ptolemy_CLI_shell_script) and [exposure target hole finding](/leginon/Leginon_Manual/New_User_Features_36/Multi-grid_autoscreening/First-time_autoscreening_setup/Setup_Ptolemy_CLI_for_exposure_targeting)
