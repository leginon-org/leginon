#
# Makefile [array/convol]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = convol

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o convol_int16.o convol_int32.o \
       convol_int8.o convol_real.o convol_uint16.o convol_uint32.o \
       convol_uint8.o max.o max_int16.o max_int32.o max_int8.o max_real.o \
       max_uint16.o max_uint32.o max_uint8.o mean.o mean_int16.o \
       mean_int32.o mean_int8.o mean_real.o mean_uint16.o mean_uint32.o \
       mean_uint8.o median.o median_int16.o median_int32.o median_int8.o \
       median_real.o median_uint16.o median_uint32.o median_uint8.o min.o \
       min_int16.o min_int32.o min_int8.o min_real.o min_uint16.o \
       min_uint32.o min_uint8.o

EXTRAOBJS =

CFLAGS = $(CLIBOPT)
CPPFLAGS = -I../config -I../../include -I../../$(LIBPRFX)include $(CPPOPT)

EXTRACLEAN =


#
# make rules
#

include ../../make/Makecommon.dirs


#
# build dependencies
#

-include Makedeps
