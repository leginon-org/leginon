#!/bin/csh

setenv APPIONDIR /home/`whoami`/pyappion
setenv PYTHONPATH ${APPIONDIR}/lib:${PYTHONPATH}
setenv LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:/ami/sw/lib
pathmgr -var PATH promote $APPIONDIR/particle_manager
pathmgr -var PATH promote $APPIONDIR/ace
setenv FINDEM_EXE ${APPIONDIR}/particle_manager/findem.exe
setenv MATLABPATH ${MATLABPATH}:${APPIONDIR}/ace

#setenv FINDEM_EXE /ami/sw/packages/FindEM/FindEM_SB
#setenv SELEXON_PATH /ami/sw/packages/selexon

