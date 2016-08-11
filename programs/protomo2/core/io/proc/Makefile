#
# Makefile [io/proc]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = heapproc

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o heapfile.o heapmem.o heapmemproc.o \
       heapmmapproc.o heapnest.o heapnestproc.o heapstdproc.o \
       heapsysproc.o

EXTRAOBJS =

CFLAGS = $(CLIBOPT)
CPPFLAGS = -I../config -I ../heap -I../../include -I../../$(LIBPRFX)include $(CPPOPT)

EXTRACLEAN =


#
# make rules
#

include ../../make/Makecommon.dirs


#
# build dependencies
#

-include Makedeps
