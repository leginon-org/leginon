#
# Makefile [fourier/gslfft]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include ../../Makedefs

LIBMAJOR = 2

LIBMINOR = 1.0

PRFX = gslfft

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o gslfftcmplxtransf.o \
       gslfftinvcmplxtransf.o gslfftinvrealtransf.o gslfftrealtransf.o

EXTRAOBJS = 

SOLIBS = -L../../lib -l$(LIBPRFX)fourier -l$(LIBPRFX)core $(LIBGSLFFT)

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
