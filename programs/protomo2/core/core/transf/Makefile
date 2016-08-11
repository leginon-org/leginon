#
# Makefile [core/transf]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include ../../Makedefs

PRFX = transf

INCS = $(PRFX).h $(PRFX)module.h transfdefs.h transf2.h transf3.h transfn.h

OBJS = $(PRFX).o $(PRFX)module.o transf2diag.o transf2inv.o transf2mul.o \
       transf2transl.o transf2transpmulvec.o transf2unit.o transf3diag.o \
       transf3inv.o transf3mul.o transf3transl.o transf3transpmulvec.o \
       transf3unit.o transfdiag.o transfinv.o transfmul.o transftransl.o \
       transftranspmulvec.o transfunit.o

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
