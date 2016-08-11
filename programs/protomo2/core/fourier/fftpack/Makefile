#
# Makefile [fourier/fftpack]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include ../../Makedefs

LIBMAJOR = 2

LIBMINOR = 1.0

PRFX = fftpack

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o fftpackcmplxtransf.o \
       fftpackinvcmplxtransf.o fftpackinvrealtransf.o \
       fftpackrealeventransf.o fftpackrealoddtransf.o fftpackrealtransf.o

EXTRAOBJS = cfftb1.o cfftf1.o cffti1.o passb.o passb2.o passb3.o passb4.o passb5.o \
            passf.o passf2.o passf3.o passf4.o passf5.o radb2.o radb3.o radb4.o \
            radb5.o radbg.o radf2.o radf3.o radf4.o radf5.o radfg.o rfftb1.o \
            rfftf1.o rffti1.o

SOLIBS = -L../../lib -l$(LIBPRFX)fourier -l$(LIBPRFX)core

CFLAGS = $(CLIBOPT)
CPPFLAGS = -I../config -I../fourier -I../../include $(CPPOPT)

FFLAGS = $(FLIBOPT)


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
