#
# Makefile [approx/neldermead]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include ../../Makedefs

PRFX = nmmin

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o neldermead.o

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
