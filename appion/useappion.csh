setenv APPIONDIR ~/pyappion
setenv PYTHONPATH ${PYTHONPATH}:${APPIONDIR}/lib
setenv LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:${APPIONDIR}/lib
set path = ( $path $APPIONDIR/particle_manager )
setenv FINDEMEXE ${APPIONDIR}/particle_manager/findem.exe

