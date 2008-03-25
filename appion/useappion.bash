#!/bin/bash

export APPIONDIR="/home/`whoami`/pyappion"
export PYTHONPATH="${APPIONDIR}/lib:${PYTHONPATH}"
export PATH="$APPIONDIR/bin:${PATH}"
export MATLABPATH="${MATLABPATH}:${APPIONDIR}/ace"

### Legacy
#export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/ami/sw/lib"
#export FINDEM_EXE="${APPIONDIR}/bin/findem.exe"
#export FINDEM_EXE="/ami/sw/packages/FindEM/FindEM_SB"
#export SELEXON_PATH="/ami/sw/packages/selexon"
