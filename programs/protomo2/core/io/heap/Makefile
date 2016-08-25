#
# Makefile [io/heap]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = heap

INCS = $(PRFX).h $(PRFX)module.h $(PRFX)debug.h

OBJS = $(PRFX).o $(PRFX)module.o heapaccess.o heapalloc.o heapdealloc.o \
       heapdebug.o heapdir.o heapextend.o heapfinal.o heapflush.o \
       heapget.o heapinit.o heapmeta.o heapnew.o heapresize.o heapseg.o \
       heapstat.o heapsync.o

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
