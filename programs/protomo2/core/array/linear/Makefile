#
# Makefile [array/linear]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = linear

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o linear_2d_int16_int16.o \
       linear_2d_int16_real.o linear_2d_int32_int32.o \
       linear_2d_int32_real.o linear_2d_int8_int8.o linear_2d_int8_real.o \
       linear_2d_real.o linear_2d_real_real.o linear_2d_uint16_real.o \
       linear_2d_uint16_uint16.o linear_2d_uint32_real.o \
       linear_2d_uint32_uint32.o linear_2d_uint8_real.o \
       linear_2d_uint8_uint8.o linear_3d_int16_int16.o \
       linear_3d_int16_real.o linear_3d_int32_int32.o \
       linear_3d_int32_real.o linear_3d_int8_int8.o linear_3d_int8_real.o \
       linear_3d_real.o linear_3d_real_real.o linear_3d_uint16_real.o \
       linear_3d_uint16_uint16.o linear_3d_uint32_real.o \
       linear_3d_uint32_uint32.o linear_3d_uint8_real.o \
       linear_3d_uint8_uint8.o linear_real.o

CFLAGS = $(CLIBOPT)
CPPFLAGS = -I../config -I../statistics -I../transfer -I../transform -I../../include $(CPPOPT)


#
# make rules
#

include ../../make/Makecommon.dirs


#
# build dependencies
#

-include Makedeps
