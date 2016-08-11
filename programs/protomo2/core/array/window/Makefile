#
# Makefile [array/window]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = window

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o windowcut.o windowextract.o \
       windowresample.o windowsample.o

EXTRAOBJS = 

CFLAGS = $(CLIBOPT)
CPPFLAGS = -I../config -I../../include $(CPPOPT)

EXTRACLEAN = 


#
# make rules
#

include ../../make/Makecommon.dirs


#
# build dependencies
#

-include Makedeps
