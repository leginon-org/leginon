#
# Makefile [align/align]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = tomoalign

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o tomoaligncommon.o tomoalignexec.o \
       tomoaligninit.o tomoalignparam.o tomoalignsearch.o \
       tomoalignseries.o tomoalignseriescorr.o tomoaligntilt.o \
       tomoalignwrite.o

EXTRAOBJS =

CFLAGS = $(CLIBOPT)
CPPFLAGS = -I../config -I../../include -I../../i3d/include $(CPPOPT)

EXTRACLEAN =


#
# make rules
#

include ../../make/Makecommon.dirs


#
# build dependencies
#

-include Makedeps
