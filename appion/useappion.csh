setenv APPIONDIR /home/`whoami`/pyappion
setenv PYTHONPATH ${PYTHONPATH}:${APPIONDIR}/lib
setenv LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:${APPIONDIR}/lib
set path = ( $path $APPIONDIR/particle_manager )
setenv FINDEM_EXE ${APPIONDIR}/particle_manager/findem.exe

