#
# Makefile [modules/protomo]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include ../../Makedefs

LIBMAJOR = 2

LIBMINOR = 1.0

PRFX = protomo

INCS = $(PRFX).h

OBJS = $(PRFX).o $(PRFX)module.o geom.o param.o series.o

EXTRAOBJS =

I3LIBS = -L../../i3d/lib -l$(LIBPRFX)fourierop -l$(LIBPRFX)fourier -l$(LIBPRFX)imageio -l$(LIBPRFX)io -l$(LIBPRFX)approx -l$(LIBPRFX)image -l$(LIBPRFX)array -l$(LIBPRFX)core
T3LIBS = -L../../i3dtomo/lib -l$(LIBPRFX)tomoalign -l$(LIBPRFX)tomoseriesmap -l$(LIBPRFX)tomoseries -l$(LIBPRFX)tomofourier -l$(LIBPRFX)tomomap -l$(LIBPRFX)tomofit -l$(LIBPRFX)tomo
P3LIBS = -L../../lib -l$(LIBPRFX)tomopy

SOLIBS = $(P3LIBS) $(T3LIBS) $(I3LIBS) $(IMGLIBS) $(LIBMINPACK) $(SYSLIBS)

CFLAGS = $(CLIBOPT)
CPPFLAGS = -I../../include -I../../i3dtomo/include -I../../i3d/include $(PYINCS) $(CPPOPT)


#
# make rules
#

include ../../Makecommon.cc


#
# build dependencies
#

-include Makedeps
