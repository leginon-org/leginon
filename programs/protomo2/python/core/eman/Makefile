#
# Makefile [modules/eman]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include ../../Makedefs

LIBMAJOR = 2

LIBMINOR = 1.0

PRFX = tomopyeman

INCS = $(PRFX).h

OBJS  = $(PRFX).o
COBJS = $(PRFX)module.o tomopyemancheck.o

EXTRAOBJS =

P3LIBS = -L../../lib -l$(LIBPRFX)tomopy
I3LIBS = -L../../i3d/lib -l$(LIBPRFX)imageio -l$(LIBPRFX)io -l$(LIBPRFX)image -l$(LIBPRFX)array -l$(LIBPRFX)core
E3LIBS = -L../../i3deman/lib -lpyEMData2 -lEM2

SOLIBS = $(P3LIBS) $(I3LIBS) $(E3LIBS) $(IMGLIBS) $(SYSLIBS)

CXXFLAGS = $(CXXLIBOPT)
CXXPPFLAGS = -I../config -I../image -I../../include -I../../i3deman/include $(PYINCS) $(CPPOPT)

CFLAGS = $(CLIBOPT)
CPPFLAGS = -I../config -I../image -I../../include -I../../i3d/include $(PYINCS) $(CPPOPT)


#
# make rules
#

include ../../Makecommon.cxx


#
# build dependencies
#

-include Makedeps
