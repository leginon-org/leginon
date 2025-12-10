Appion python scripts are often wrappers that calls scripts or command from other packages. List here are what is needed by each typically used options. Note that users may not want to use all functions as programs go out of fashion.

## Direct Detector Frame Alignment

  --------------------------------- ----------------------------- -----------------------------------
  appion script name                external package              script/command within the package
  makeDDAlignMotionCor2_UCSF.py     MotionCor2                    
  makeDDAlignMotionCorr_Purdue.py   motioncorr v2.0 from Purdue   
  makeDEAlignedSum.py               deProcessFrames.py            
  makeDEAlignedSum.py               EMAN2                         
  --------------------------------- ----------------------------- -----------------------------------

## Automated CTF Estimation

  -------------------- ------------------
  appion script name   external package
  ctffind4.py          CTFFIND4
  gctf.py              Gctf
  -------------------- ------------------

## Particle Selection

  ----------------------- ----------------------------------- ------------
  templateCorrelator.py   template-based particle selection   FindEM
  gAutomatchFast.py       template-based particle selection   Gautomatch
  ----------------------- ----------------------------------- ------------

## Particle Stack Making and manipulation

  ----------------------------- -------------------------------------------------------------------------- ------------- --------------------------------------------
  appion script name            subfunction                                                                package       script/command within the package
                                general image manipulation                                                 EMAN1         proc2d
  makestack2.py                 making Imagic stack                                                        appionlib     
  makestack2.py                 making Relion stack                                                        Relion        relion_preprocess or relion_preprocess_mpi
  makestack2.py                 CTF correction by Wiener filtering of the full image (Imagic stack only)   ace2          ace2correct.exe
  makestack2.py                 normalization by edge                                                      appionlib     
  makestack2.py/quickstack.py   making montage of stack mean/standard deviation map                        ImageMagick   montage
  centerParticleStack.py        particle centering in a stack                                              EMAN1         centeralignint
  boxMaskStack.py               soft masking of helical boxed particles in the stack                       Spider        
  sortJunkStack.py              sort particle by similarity to average                                     Xmipp2        xmipp_sort_by_statistics
  ----------------------------- -------------------------------------------------------------------------- ------------- --------------------------------------------
