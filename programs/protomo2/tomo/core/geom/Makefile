#
# Makefile [core/geom]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = tomogeom

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o tomogeomarea.o tomogeomcorr.o \
       tomogeomload.o tomogeomrot.o tomogeomsave.o

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
