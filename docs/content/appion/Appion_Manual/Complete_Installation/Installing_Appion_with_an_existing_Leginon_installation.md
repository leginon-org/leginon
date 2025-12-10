Make sure you have the latest version of [Leginon](/leginon/) installed. Then follow the steps below to install image processing packages on your Processing Server.


## Package alias table

Those not mentioned here uses the original names in the call.

------------------------------------------------------------------------

program package name version appion executable alias Accessible
MotionCor2 1.0.2 motioncor2 shell
motioncorr v2.0 from Purdue 2.0 dosefgpu_driftcorr shell
DE_process_frames.py 2.7.1 deProcessFrames.py pythonpath
ctffind4 4.1.5 ctffind4 shell
Gctf 1.06 gctfCurrent shell
ctftilt 1.5 ctftilt.exe shell
FindEM 20/10/01 findem64.exe shell
Gautomatch 0.53 gautomatch shell
Spider 18.10 spider shell
frealign 9.11 frealign_v9.exe and frealign_v9_mp.exe shell
xmipp2 cl2d* 2.4 xmipp_mpi_class_averages shell
xmipp3 cl2d* 3.1 xmipp_classify_CL2D shell
EMAN1 proc2d 1.9 proc2d shell
------------------------------------------- --------------- ------------------------------------------------------------ ------------------

- default environment is xmipp2. All other xmipp functions wraps around xmipp2.
- xmipp3 conflict with xmipp2 is resolved in appion/bin/runXmipp3CL2D.py with a line of code
csh -c 'modulecmd python load xmipp/3.1'


Change it if desired.



[Create a Test Project >](/appion/Appion_Manual/Complete_Installation/Create_a_Test_Project)
