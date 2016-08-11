#
# Makefile [series/cache]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = tomocache

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o tomocacheget.o

EXTRAOBJS =

CFLAGS = $(CLIBOPT)
CPPFLAGS = -I../config -I../file -I../../include -I../../i3d/include $(CPPOPT)

EXTRACLEAN =


#
# make rules
#

include ../../make/Makecommon.dirs


#
# build dependencies
#

-include Makedeps
