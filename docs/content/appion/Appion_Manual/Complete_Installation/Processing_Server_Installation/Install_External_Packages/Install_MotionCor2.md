
For a gpu computer used for frame alignment using MotionCor2, install [LINUX: CUDA 8.0 Production Release](https://developer.nvidia.com/cuda-downloads) (RHEL 6.x 64bit).
Then Download from http://msg.ucsf.edu/em/software/motioncor2.html and follow its installation instruction.

Make a soft link to /usr/local/bin as motioncor2 so that Appion script can find it.

ln -s your_installation_MotionCor2 /usr/local/bin/motioncor2

### Testing: type

motioncor2


should give help menu



[< Install External Packages](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_External_Packages) | [Install MotionCorr >](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Install_dosefgpu_driftcorr)
