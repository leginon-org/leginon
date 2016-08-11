#
# Makefile [core/transfer]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = tomotransfer

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o tomotransfercalc.o tomotransferfsh.o \
       tomotransferparam.o tomotransferscale.o

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
