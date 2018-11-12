#
# Makefile [array/spatial]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = spatial

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o gradcorrlin_1d_real.o \
       gradcorrlin_2d_real.o gradcorrlin_3d_real.o gradientlin_1d_real.o \
       gradientlin_2d_real.o gradientlin_3d_real.o peak_1d_real.o \
       peak_2d_real.o peak_3d_real.o peak_real.o

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
