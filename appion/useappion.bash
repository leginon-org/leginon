#!/bin/bash

export APPIONDIR="/home/`whoami`/pyappion"
export PYTHONPATH="${PYTHONPATH}:${APPIONDIR}/lib"
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/ami/sw/lib"
export PATH="${PATH}:$APPIONDIR/particle_manager:$APPIONDIR/ace"
export MATLABPATH="${MATLABPATH}:${APPIONDIR}/ace"
export FINDEM_EXE="${APPIONDIR}/particle_manager/findem.exe"

### Legacy
#export FINDEM_EXE="/ami/sw/packages/FindEM/FindEM_SB"
#export SELEXON_PATH="/ami/sw/packages/selexon"
