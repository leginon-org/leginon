#
# Makefile [align/reference]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = tomoref

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o tomorefbck.o tomorefcommon.o \
       tomorefinit.o tomorefmrg.o tomorefparam.o tomorefstart.o \
       tomoreftransform.o

EXTRAOBJS =

CFLAGS = $(CLIBOPT)
CPPFLAGS = -I../config -I../window -I../../include -I../../i3d/include $(CPPOPT)

EXTRACLEAN =


#
# make rules
#

include ../../make/Makecommon.dirs


#
# build dependencies
#

-include Makedeps
