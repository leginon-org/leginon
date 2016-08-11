#
# Makefile [array/sample]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = sample

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o sample_2d_int16_int16.o \
       sample_2d_int16_real.o sample_2d_int32_int32.o \
       sample_2d_int32_real.o sample_2d_int8_int8.o sample_2d_int8_real.o \
       sample_2d_real.o sample_2d_real_real.o sample_2d_uint16_real.o \
       sample_2d_uint16_uint16.o sample_2d_uint32_real.o \
       sample_2d_uint32_uint32.o sample_2d_uint8_real.o \
       sample_2d_uint8_uint8.o sample_3d_int16_int16.o \
       sample_3d_int16_real.o sample_3d_int32_int32.o \
       sample_3d_int32_real.o sample_3d_int8_int8.o sample_3d_int8_real.o \
       sample_3d_real.o sample_3d_real_real.o sample_3d_uint16_real.o \
       sample_3d_uint16_uint16.o sample_3d_uint32_real.o \
       sample_3d_uint32_uint32.o sample_3d_uint8_real.o \
       sample_3d_uint8_uint8.o sample_box.o sample_real.o

CFLAGS = $(CLIBOPT)
CPPFLAGS = -I../config -I../statistics -I../transfer -I../../include $(CPPOPT)


#
# make rules
#

include ../../make/Makecommon.dirs


#
# build dependencies
#

-include Makedeps
