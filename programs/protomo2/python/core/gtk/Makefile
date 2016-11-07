#
# Makefile [core/gtk]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include ../../Makedefs

LIBMAJOR = 2

LIBMINOR = 1.0

PRFX = tomopygtk

INCS = $(PRFX).h

OBJS = $(PRFX)module.o

EXTRAOBJS =

P3LIBS = -L../../lib -l$(LIBPRFX)tomopy
I3LIBS = -L../../i3d/lib -l$(LIBPRFX)imageio -l$(LIBPRFX)io -l$(LIBPRFX)image -l$(LIBPRFX)array -l$(LIBPRFX)core
G3LIBS = -L../../i3dgui/lib -l$(LIBPRFX)gtk -l$(LIBPRFX)gui

SOLIBS = $(G3LIBS) $(P3LIBS) $(I3LIBS) $(IMGLIBS) $(GTKLIBS) $(GTKGLLIBS) $(OPENGLLIBS) $(SYSLIBS)

CFLAGS = $(CLIBOPT)
CPPFLAGS = -I../config -I../../include -I../../i3dgui/include -I../../i3d/include $(PYINCS) $(CPPOPT)


#
# make rules
#

include ../../Makecommon.cc


#
# build dependencies
#

-include Makedeps
