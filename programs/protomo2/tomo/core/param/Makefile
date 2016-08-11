#
# Makefile [core/param]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include   ../../Makedefs

PRFX = tomoparam

INCS = $(PRFX).h $(PRFX)module.h

OBJS = $(PRFX).o $(PRFX)module.o tomoparamcommon.o tomoparamdebug.o \
       tomoparamdup.o tomoparamread.o tomoparamsemant.o tomoparamset.o \
       tomoparamwrite.o

EXTRAOBJS = tomoparamlexer.o tomoparamparser.tab.o

CFLAGS = $(CLIBOPT) -D_POSIX_SOURCE
CPPFLAGS = -I../config -I../../include -I../../i3d/include $(CPPOPT)

EXTRACLEAN = tomoparamlexer.c tomoparamparser.tab.[ch] tomoparamparser.output

ifeq ($(CC),gcc)
  CFLAGS += -Wno-sign-compare
endif


#
# make rules
#

include ../../make/Makecommon.dirs

tomoparamparser.tab.c: tomoparamparser.y
	bison -v -d --debug tomoparamparser.y

tomoparamlexer.c: tomoparamlexer.l tomoparamparser.tab.c
	flex -s -d -otomoparamlexer.c tomoparamlexer.l


#
# build dependencies
#

-include Makedeps

$(PRFX).o: $(EXTRAOBJS)
