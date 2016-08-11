#
# Makefile [core/stringtable]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = stringtable

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o stringtablecopy.o stringtableinsert.o \
       stringtablelookup.o

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
