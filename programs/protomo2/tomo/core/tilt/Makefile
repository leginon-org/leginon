#
# Makefile [core/tilt]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = tomotilt

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o tomotiltcommon.o tomotiltcooref.o \
       tomotiltdup.o tomotiltget.o tomotiltmat.o tomotiltmataxis.o \
       tomotiltmatorient.o tomotiltnew.o tomotiltread.o tomotiltsemant.o \
       tomotiltsort.o tomotiltwrite.o

EXTRAOBJS = tomotiltlexer.o tomotiltparser.tab.o

CFLAGS = $(CLIBOPT) -D_POSIX_SOURCE
CPPFLAGS = -I../config -I../../include -I../../i3d/include $(CPPOPT)

EXTRACLEAN = tomotiltlexer.c tomotiltparser.tab.[ch] tomotiltparser.output

ifeq ($(CC),gcc)
  CFLAGS += -Wno-sign-compare
endif


#
# make rules
#

include ../../make/Makecommon.dirs

tomotiltparser.tab.c: tomotiltparser.y
	bison -v -d --debug tomotiltparser.y

tomotiltlexer.c: tomotiltlexer.l tomotiltparser.tab.c
	flex -s -d -otomotiltlexer.c tomotiltlexer.l


#
# build dependencies
#

-include Makedeps

$(PRFX).o: $(EXTRAOBJS)
