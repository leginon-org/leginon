#
# Makefile [fourier/fourier]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include ../../Makedefs

PRFX = fourier

INCS = $(PRFX).h $(PRFX)module.h fouriermode.h

OBJS = $(PRFX).o $(PRFX)module.o fouriercenter.o fouriercmplx.o \
       fouriercmplxinit.o fouriercmplxtransf.o fourierimag.o \
       fourierimaginit.o fourierimagtransf.o fourierinvcmplx.o \
       fourierinvcmplxinit.o fourierinvcmplxtransf.o fourierinvimag.o \
       fourierinvimaginit.o fourierinvimagtransf.o fourierinvreal.o \
       fourierinvrealinit.o fourierinvrealtransf.o fourierreal.o \
       fourierrealinit.o fourierrealtransf.o

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
