#
# Makefile [core/matrix]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include ../../Makedefs

PRFX = mat

INCS = $(PRFX).h $(PRFX)module.h matdefs.h mat2.h mat3.h mat4.h matn.h matmn.h

OBJS = $(PRFX).o $(PRFX)module.o mat2diag.o mat2inv.o mat2mul.o \
       mat2multransp.o mat2mulvec.o mat2rot.o mat2rotinv.o mat2svd.o \
       mat2transp.o mat2transpmul.o mat2transpmulvec.o mat2unit.o \
       mat2vecmul.o mat3diag.o mat3euler.o mat3inv.o mat3mul.o \
       mat3multransp.o mat3mulvec.o mat3rot.o mat3rotaxis.o mat3rotdir.o \
       mat3rotinv.o mat3rotx.o mat3roty.o mat3rotz.o mat3svd.o \
       mat3transp.o mat3transpmul.o mat3transpmulvec.o mat3unit.o \
       mat3vecmul.o mat4diag.o mat4inv.o mat4mul.o mat4multransp.o \
       mat4mulvec.o mat4svd.o mat4transp.o mat4transpmul.o \
       mat4transpmulvec.o mat4unit.o mat4vecmul.o matdiag.o matgauss.o \
       matmul.o matndiag.o matninv.o matnmul.o matnmultransp.o \
       matnmulvec.o matntransp.o matntranspmul.o matntranspmulvec.o \
       matnunit.o matnvecmul.o matsvd.o mattransp.o matunit.o

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
