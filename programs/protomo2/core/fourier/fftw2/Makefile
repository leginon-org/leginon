#
# Makefile [fourier/fftw2]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include ../../Makedefs

LIBMAJOR = 2

LIBMINOR = 1.0

PRFX = fftw2

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o fftw2cmplxtransf.o fftw2invcmplxtransf.o \
       fftw2invrealtransf.o fftw2realtransf.o

EXTRAOBJS =

SOLIBS = -L../../lib -l$(LIBPRFX)fourier -l$(LIBPRFX)core $(LIBFFTW2)

CFLAGS = $(CLIBOPT)
CPPFLAGS = -I../config -I../fourier -I../../include $(CPPOPT)


#
# make rules
#

ifdef SO
  include ../../make/Makecommon.extradirs
else
  include ../../make/Makecommon.dirs
endif


#
# build dependencies
#

-include Makedeps
