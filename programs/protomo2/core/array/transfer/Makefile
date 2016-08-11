#
# Makefile [array/transfer]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = transfer

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o scale_cmplx.o scale_cmplx_cmplx.o \
       scale_imag.o scale_imag_cmplx.o scale_int16_real.o \
       scale_int32_real.o scale_int8_real.o scale_real.o \
       scale_real_cmplx.o scale_real_int16.o scale_real_int32.o \
       scale_real_int8.o scale_real_real.o scale_real_uint16.o \
       scale_real_uint32.o scale_real_uint8.o scale_type.o \
       scale_uint16_real.o scale_uint32_real.o scale_uint8_real.o

CFLAGS = $(CLIBOPT)
CPPFLAGS = -I../config -I../../include $(CPPOPT)


#
# make rules
#

include ../../make/Makecommon.dirs


#
# build dependencies
#

-include Makedeps
