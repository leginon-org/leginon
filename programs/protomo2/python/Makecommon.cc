#
# Makecommon.cc: common rules for subdirectories
#
# Copyright © 2012 Hanspeter Winkler
#


LIBDIR = ../../lib

LIBNAME = $(PRFX)

LIBNAMESO = $(LIBNAME).so.$(LIBMAJOR)

LIBNAMEFULL = $(LIBNAMESO).$(LIBMINOR)

LIB = $(LIBDIR)/$(LIBNAME).a

LIBSO = $(LIBDIR)/$(LIBNAMEFULL)


#
# make rules
#

.PHONY: help all install clean distclean depend makedate

help:
	@ echo "usage: make [ all | install | depend | clean | distclean ]"

all install: Makeincs makedate $(OBJS) $(EXTRAOBJS) $(LIB) $(LIBSO)

clean:
	rm -f Makeincs makedate.h *.o *.a *.so *.so.* $(EXTRACLEAN) a.out core *.i *.s *.L *~ *# .#*

distclean: clean
	rm -f Makedeps

depend: Makeincs makedate
	$(CC) $(CPPFLAGS) $(CFLAGS) -MM $(OBJS:.o=.c) >Makedeps

makedate:
	@ ../../make/getdate.sh >makedate.h

Makeincs: $(INCS)
	$(MAKE) -C ../../include DIR=$(CURDIR) $(INCS)
	@ touch Makeincs


#
# make libraries
#

$(LIB): $(OBJS) $(EXTRAOBJS)
	$(AR) $(AROPT) $@ $(OBJS) $(EXTRAOBJS)

$(LIBSO): $(LIB)
	$(SO) $(SOOPT) $(SONAME)$(LIBNAMESO) -o $@ $(SOOPTOBJ) $< $(SOOPTEND) $(SOLIBS)
	$(STRIP) $(STRIPOPT) $@
	rm -f $(LIBDIR)/$(LIBNAMESO) $(LIBDIR/$(LIBNAME).so
	ln -s $(LIBNAMEFULL) $(LIBDIR)/$(LIBNAMESO)
	ln -s $(LIBNAMEFULL) $(LIBDIR)/$(LIBNAME).so
