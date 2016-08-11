#
# Makefile [imageio/ccp4io]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include ../../Makedefs

LIBMAJOR = 2

LIBMINOR = 1.0

PRFX = ccp4io

INCS = $(PRFX)defs.h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o ccp4ioextra.o ccp4iofmt.o ccp4ioget.o \
       ccp4ionew.o ccp4ioold.o ccp4iosiz.o

EXTRAOBJS =

SOLIBS = -L../../lib -l$(LIBPRFX)imageio -l$(LIBPRFX)io -l$(LIBPRFX)image -l$(LIBPRFX)array -l$(LIBPRFX)core

CFLAGS = $(CLIBOPT)
CPPFLAGS = -I../config -I../common -I../../include $(CPPOPT)


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
