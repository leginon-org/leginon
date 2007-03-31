#!/bin/bash

export APPIONDIR="/home/`whoami`/pyappion"
export PYTHONPATH="${PYTHONPATH}:${APPIONDIR}/lib"
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/ami/sw/lib"
export PATH="${PATH}:$APPIONDIR/particle_manager:$APPIONDIR/ace"
export MATLABPATH="${MATLABPATH}:${APPIONDIR}/ace"

export FINDEM_EXE="${APPIONDIR}/particle_manager/findem.exe"
#export FINDEM_EXE="/ami/sw/packages/FindEM/FindEM_SB"
