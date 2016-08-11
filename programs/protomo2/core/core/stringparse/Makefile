#
# Makefile [core/stringparse]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = stringparse

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o stringparsebool.o stringparsecmplx32.o \
       stringparsecmplx64.o stringparsedatetime.o stringparseident.o \
       stringparseimag32.o stringparseimag64.o stringparseint16.o \
       stringparseint32.o stringparseint64.o stringparseint8.o \
       stringparsekeyword.o stringparsekeywordcase.o stringparselist.o \
       stringparsepair.o stringparserange.o stringparsereal32.o \
       stringparsereal64.o stringparseselection.o stringparsestring.o \
       stringparsestringcase.o stringparseuint16.o stringparseuint32.o \
       stringparseuint64.o stringparseuint8.o

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
