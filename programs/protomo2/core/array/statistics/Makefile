#
# Makefile [array/statistics]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = statistics

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o histogram.o histogramcalc.o \
       histogramcalcimag.o histogramcalcint16.o histogramcalcint32.o \
       histogramcalcint8.o histogramcalcreal.o histogramcalcuint16.o \
       histogramcalcuint32.o histogramcalcuint8.o histogramimag.o \
       histogramint16.o histogramint32.o histogramint8.o histogramreal.o \
       histogramuint16.o histogramuint32.o histogramuint8.o minmaxmean.o \
       minmaxmeancmplx.o minmaxmeanimag.o minmaxmeanint16.o \
       minmaxmeanint32.o minmaxmeanint8.o minmaxmeanreal.o \
       minmaxmeanuint16.o minmaxmeanuint32.o minmaxmeanuint8.o \
       sumabs2cmplx.o sumabs2real.o zeromeancmplx.o zeromeanreal.o

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
