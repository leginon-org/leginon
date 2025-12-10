
The .appion.cfg file is used to automatically create job files and submit them to your job submission server. The example file provided below works for the Torque Resource Manager.
Instructions for installing Torque appear as a later step in this manual under the [Setup Remote Processing](/appion/Appion_Manual/Complete_Installation/Setup_Remote_Processing) section.

1. Create a hidden file called .appion.cfg in the myami directory, at one level above where appionlib reside as the configuration for all users
For example, from python command prompt
import appionlib
appionlib


gives
<module 'appionlib' from '/usr/lib/python26/site-packages/appionlib/*init*.pyc'>


then the path where appion looks for this global configuration file is
/usr/lib/python26/.appion.cfg

**Note:** This file may be added to a users home directory on the processing host to override the configuration found in the installation directory.
 

1. Add the following contents:
ProcessingHostType=Torque

Shell=/bin/csh

ScriptPrefix=

ExecCommand=/usr/local/bin/qsub

StatusCommand=/usr/local/bin/qstat

AdditionalHeaders= -m e, -j oe

PreExecuteLines=
2. Modify the settings for your Processing Host. For example, you can specify "SGE" if your processingHostType uses the Sun Grid Engine scheduler or /bin/bash if your shell is bash.



[< Configure sinedon.cfg](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Configure_sinedoncfg) | [Install External Packages >](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_External_Packages)
