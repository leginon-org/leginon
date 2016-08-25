#
# Makefile [io/i3io]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = i3io

INCS = $(PRFX).h $(PRFX)module.h $(PRFX)array.h $(PRFX)debug.h $(PRFX)nest.h

OBJS = $(PRFX).o $(PRFX)module.o i3ioaddr.o i3ioarray.o i3iobeginend.o \
       i3iobeginendalloc.o i3iobeginendsegm.o i3ioclose.o i3iocommon.o \
       i3iodebug.o i3iofile.o i3ioflush.o i3ioget.o i3ionest.o i3ioread.o \
       i3iowrite.o

CFLAGS = $(CLIBOPT)
CPPFLAGS = -I../config -I ../heap -I ../proc -I../../include $(CPPOPT)


#
# make rules
#

include ../../make/Makecommon.dirs


#
# build dependencies
#

-include Makedeps
