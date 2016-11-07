#
# Makefile [core/stringformat]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = stringformat

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o stringformatdatetime.o \
       stringformatstring.o stringformatuint64.o

CFLAGS = $(CLIBOPT)
CPPFLAGS = -I../config -I../base $(CPPOPT)


#
# make rules
#

include ../../make/Makecommon.dirs


#
# build dependencies
#

-include Makedeps
