#
# Makefile [io/fileio]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include ../../Makedefs

PRFX = fileio

INCS = $(PRFX).h $(PRFX)module.h $(PRFX)checksum.h

OBJS = $(PRFX).o $(PRFX)module.o fileioaccess.o fileioallocate.o \
       fileiochecksum.o fileioclose.o fileioflush.o fileioget.o \
       fileiolock.o fileiomap.o fileioopen.o fileioopenmap.o \
       fileioopenstd.o fileioread.o fileioreadstd.o fileioset.o \
       fileiostatus.o fileiostd.o fileiotruncate.o fileiounlink.o \
       fileiounmap.o fileiowrite.o fileiowritestd.o

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
