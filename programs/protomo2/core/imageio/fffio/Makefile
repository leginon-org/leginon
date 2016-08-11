#
# Makefile [imageio/fffio]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include ../../Makedefs

PRFX = fffio

INCS = $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o fffioextra.o fffiofin.o fffiofmt.o \
       fffioget.o fffionew.o fffioold.o fffiosiz.o

CFLAGS = $(CLIBOPT)
CPPFLAGS = -I../config -I../common -I../../include $(CPPOPT)


#
# make rules
#

include ../../make/Makecommon.dirs


#
# build dependencies
#

-include Makedeps
