
Appion scripts interact with external packages in one of the two ways: Executing a shell command, or through python call. The name of the file in the call may not be the same as the standard installation as described by the package distributor.

If it is accessed from shell, you should either create soft link (preferred) or rename the file you downloaded (not best practice since you may get confused later. Test its accessibility from the environment you would run appion script.

For example, ctffin4 of whatever version would typically installed in /usr/local/bin. The executable file in there is called ctffind4.exe. You should do

cd /usr/local/bin
ln -s ctffind64.exe ctffind4

Next time, when you start a shell, try:

which ctffind4


It should be able to find the link and the actual executable file.ctffind64.exe

For files called through python, the file need to be in the environment variable PYTHONPATH You can test it in the appion environment with an import test.

python
python> import deProcessFrames

## Program/module call alias name in Appion (myami-3.3, myami-beta branches, and trunk)

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
---------------------------------------------------------------- ---------------------- ------------------------------------------------------------------------------------------ ---------------------------

- default environment is xmipp2. All other xmipp functions wraps around xmipp2.
- xmipp3 conflict with xmipp2 is resolved in appion/bin/runXmipp3CL2D.py with a line of code
csh -c 'modulecmd python load xmipp/3.1'


Change it if desired.


## Installation

[External Package requirement of Appion scripts](/appion/Processing_Server_External_Packages_Installation/External_Package_requirement_of_Appion_scripts)

### Required for preprocessing pipeline up to stack making for Relion/CryoSparc

1.  [Configure .appion.cfg](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Configure_appioncfg)
2.  [Install External Packages](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_External_Packages)
3.  [MotionCor2](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_dosefgpu_driftcorr/Install_motioncor2_shared)
4.  [Install Gctf](/appion/Install_Gctf)
5.  Install CtfFind. See [Install Grigorieff lab software](/appion/Install_Grigorieff_lab_software)

### Recommended for preprocessing pipelin particle picking

1.  [Compile FindEM](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Compile_FindEM)

### Required for 2D classification and other functions

1.  [Install EMAN](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_EMAN) (Only works for CentOS 6)
2.  [Install EMAN2](/appion/Install_EMAN2)
3.  [Install SPIDER](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_SPIDER)
4.  [Install Xmipp](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_Xmipp) (Xmipp2 Only works for CentOS 6)
5.  [Install UCSF Chimera](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_UCSF_Chimera)
6.  [Install Ace2](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_Ace2)
7.  [Install Imod](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_Imod)
8.  [Install Protomo2](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_Protomo2)
9.  [Install EM Hole Finder](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_EM_Hole_Finder)

### Older packages, install only if you still want to use them

1.  [MotionCorr](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_dosefgpu_driftcorr) (optional)
2.  [Install SIMPLE](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_SIMPLE)

### Testing

1.  [Test Appion](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Test_Appion)
