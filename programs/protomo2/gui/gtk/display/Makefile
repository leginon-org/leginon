#
# Makefile [gtk/display]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = guigtkdisplay

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o callbacks.o guigtkdisplay.o \
       guigtkdisplaycommon.o guigtkdisplayhisto.o guigtkdisplayimage.o \
       guigtkdisplaymodule.o interface.o support.o

EXTRAOBJS =

CFLAGS = $(CLIBOPT)
CPPFLAGS = -I../config -I../../include -I../../i3d/include $(GTKGLINCS) $(CPPOPT)

EXTRACLEAN =


#
# make rules
#

include ../../make/Makecommon.dirs


#
# build dependencies
#

-include Makedeps
