setenv APPIONDIR /home/`whoami`/pyappion
setenv PYTHONPATH ${PYTHONPATH}:${APPIONDIR}/lib
setenv LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:/ami/sw/lib
set path = ( $path $APPIONDIR/particle_manager )
setenv FINDEM_EXE ${APPIONDIR}/particle_manager/findem.exe
#setenv FINDEM_EXE /ami/sw/packages/FindEM/FindEM_SB
