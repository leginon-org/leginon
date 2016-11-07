#
# Makefile [array/array]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = array

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o arraybox.o arrayboxctr.o arraycut.o \
       arraycutpaste.o arrayelement.o arrayelementoffs.o arrayfill.o \
       arrayfnbox.o arrayfnboxctr.o arrayfncut.o arrayfncutpaste.o \
       arrayoffset.o arraysize.o

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
