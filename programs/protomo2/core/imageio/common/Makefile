#
# Makefile [imageio/common]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include ../../Makedefs

PRFX = imageio

INCS = $(PRFX).h $(PRFX)module.h $(PRFX)checksum.h

OBJS = $(PRFX).o $(PRFX)module.o imageioaddr.o imageioamap.o \
       imageiobeginend.o imageioblock.o imageiocap.o imageiochecksum.o \
       imageioclose.o imageiocommon.o imageiocreate.o imageiodefault.o \
       imageiodel.o imageioformat.o imageioget.o imageioin.o \
       imageiommap.o imageiomode.o imageioopen.o imageioout.o \
       imageioread.o imageioresize.o imageiostd.o imageiowrite.o

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
