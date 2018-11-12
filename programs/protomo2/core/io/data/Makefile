#
# Makefile [io/data]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = i3data

INCS = $(PRFX).h $(PRFX)module.h $(PRFX)defs.h

OBJS = $(PRFX).o $(PRFX)module.o i3dataimage.o i3dataprint.o

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
