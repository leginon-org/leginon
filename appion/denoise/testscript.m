clc; close all; clear all;
%%%% These paths will most likely need to be changed.
addpath('./SDKs/ksvdbox13/'... KSVD-Box V13 path
,'./SDKs/ompbox10/',... OMP-Box V10 path
    './SDKs/EMIODist/') % MRC reader Path

mrcpath = './data/'; %Pat to data
mrcname = '12jun18b_c_00032gr_00031sq_v02_00003hl_v02_00003ed_st.mrc'; %filename
savepath = './results/'; %save location, mrc files will be saved to savepath/mrc/


% See functions for more info on parameters.
[ksvdparams] = makeKSVDparams(8,64,5); %(blocksize,dictsize,sigma)
[stackparams] = makeStackparams(40,4,50,[1 1 inf inf]); %(Average Window Length, Average Start Location, Total Frame Read,ROI)

KSVDDenoiseMRC(mrcpath,mrcname,savepath,stackparams,ksvdparams)
