#!/bin/csh

setenv APPIONDIR /home/glander/pyappion
setenv PYTHONPATH ${APPIONDIR}/lib:${PYTHONPATH}
setenv PATH ${APPIONDIR}/bin:${PATH}
setenv MATLABPATH ${MATLABPATH}:${APPIONDIR}/ace

#setenv LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:/ami/sw/lib
#setenv FINDEM_EXE /ami/sw/packages/FindEM/FindEM_SB
#setenv SELEXON_PATH /ami/sw/packages/selexon

