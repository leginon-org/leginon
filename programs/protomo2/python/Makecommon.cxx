#
# Makecommon.cxx: common rules for subdirectories
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

all install: Makeincs makedate $(OBJS) $(COBJS) $(EXTRAOBJS) $(LIB) $(LIBSO)

clean:
	rm -f Makeincs makedate.h *.o *.a *.so *.so.* $(EXTRACLEAN) a.out core *.i *.s *.L *~ *# .#*

distclean: clean
	rm -f Makedeps

depend: Makeincs makedate
	$(CXX) $(CXXPPFLAGS) $(CXXFLAGS) -MM $(OBJS:.o=.cpp) >Makedeps
	$(CC) $(CPPFLAGS) $(CFLAGS) -MM $(COBJS:.o=.c) >>Makedeps

makedate:
	@ ../../make/getdate.sh >makedate.h

Makeincs: $(INCS)
	$(MAKE) -C ../../include DIR=$(CURDIR) $(INCS)
	@ touch Makeincs

$(OBJS): %.o: %.cpp
	$(CXX) $(CXXPPFLAGS) $(CXXFLAGS) -c $< -o $@

$(COBJS): %.o: %.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@


#
# make libraries
#

$(LIB): $(OBJS) $(COBJS) $(EXTRAOBJS)
	$(AR) $(AROPT) $@ $(OBJS) $(COBJS) $(EXTRAOBJS)

$(LIBSO): $(LIB)
	$(SO) $(SOOPT) $(SONAME)$(LIBNAMESO) -o $@ $(SOOPTOBJ) $< $(SOOPTEND) $(SOLIBS)
	$(STRIP) $(STRIPOPT) $@
	rm -f $(LIBDIR)/$(LIBNAMESO) $(LIBDIR/$(LIBNAME).so
	ln -s $(LIBNAMEFULL) $(LIBDIR)/$(LIBNAMESO)
	ln -s $(LIBNAMEFULL) $(LIBDIR)/$(LIBNAME).so
