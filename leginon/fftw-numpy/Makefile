# This Makefile gives the general idea
#  of how to compile these modules.
#
#  Once they are made they go into a directory on your PYTHONPATH
#
#  Note that the includes it is looking for are a little different than the
#   basic fftw install:  fftw.h
#  see the README file
#

# This should obviously be changed to reflect your system 

INCLUDES=-I/home/suloway/python-2.3-leginon-2-build/python-2.3-build/install/include/python2.3 -DHAVE_CONFIG_H -I/home/suloway/python-2.3-leginon-2-build/python-2.3-build/install/lib/python2.3/config -I/home/suloway/python-2.3-leginon-2-build/python-2.3-build/install/include/python2.3/Numeric


INSTALLDIR=..
#
# These are the fftw libraries you need to have installed to link with 
#   I link with them as shared libraries.
#
#  Version used = fftw-2.1.3
#
# Note I have two versions of the libraries one with floats as base element
#   and one as double.  You can make one or both.
#
FFTWLIB_FLOAT=sfftw
RFFTWLIB_FLOAT=srfftw
FFTWLIB_DOUBLE=dfftw
RFFTWLIB_DOUBLE=drfftw

FFTWF=-l$(FFTWLIB_FLOAT) -l$(RFFTWLIB_FLOAT)
FFTW=-l$(FFTWLIB_DOUBLE) -l$(RFFTWLIB_DOUBLE)


sfftw: 
	gcc -fPIC -c sfftw_wrap.c $(INCLUDES) 
	ld -shared sfftw_wrap.o -o sfftwmodule.so $(FFTWF)

fftw:
	gcc -fPIC -c fftw_wrap.c $(INCLUDES)
	ld -shared fftw_wrap.o -o fftwmodule.so $(FFTW)

fftw_install:
	cp fftwmodule.so $(INSTALLDIR)

sfftw_install:
	cp sfftwmodule.so $(INSTALLDIR)

swig:
	swig -python -dhtml -o sfftw_wrap.c sfftw.i
	swig -python -dhtml -o fftw_wrap.c fftw.i




