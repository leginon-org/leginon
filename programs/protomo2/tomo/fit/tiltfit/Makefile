#
# Makefile [fit/tiltfit]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = tomotiltfit

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o tomotiltfitparam.o

CFLAGS = $(CLIBOPT)
CPPFLAGS = -I../config -I../../include -I../../i3d/include $(CPPOPT)


#
# make rules
#

include ../../make/Makecommon.dirs


#
# build dependencies
#

-include Makedeps
