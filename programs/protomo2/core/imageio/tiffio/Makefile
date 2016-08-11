#
# Makefile [imageio/tiffio]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include ../../Makedefs

LIBMAJOR = 2

LIBMINOR = 1.0

PRFX = tiffio

INCS = $(PRFX)defs.h $(PRFX)module.h

OBJS = $(PRFX)module.o tiffiocommon.o tiffiofin.o tiffiofmt.o \
       tiffioget.o tiffionew.o tiffioold.o tiffiord.o tiffiosyn.o \
       tiffiotiles.o tiffiowr.o

EXTRAOBJS =

SOLIBS = -L../../lib -l$(LIBPRFX)imageio -l$(LIBPRFX)io -l$(LIBPRFX)image -l$(LIBPRFX)array -l$(LIBPRFX)core $(LIBTIFF)

CFLAGS = $(CLIBOPT)
CPPFLAGS =-I../config  -I../common -I../../include $(CPPOPT)


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
