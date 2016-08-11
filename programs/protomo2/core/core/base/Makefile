#
# Makefile [core/base]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = base

INCS = $(PRFX).h $(PRFX)module.h baselib.h exception.h message.h module.h signals.h

OBJS = $(PRFX).o $(PRFX)module.o exception.o factor.o message.o module.o \
       mulint32.o mulint64.o mulsize.o selection.o signals.o swap16.o \
       swap32.o swap64.o timeget.o

CFLAGS = $(CLIBOPT)
CPPFLAGS = -I../config $(CPPOPT)


#
# make rules
#

include ../../make/Makecommon.dirs


#
# build dependencies
#

-include Makedeps
