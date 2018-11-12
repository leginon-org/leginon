#
# Makefile [io/common]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include ../../Makedefs

PRFX = io

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o iodir.o ioident.o iopath.o iopathlist.o \
       iotemp.o

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
