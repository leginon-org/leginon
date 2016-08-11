#
# Makefile [lib]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include ../Makedefs


#
# make rules
#

.PHONY: help all install clean distclean depend

help:
	@ echo "usage: make [ all | install | depend | clean | distclean ]"

all:

install:
	$(INSTALL) $(INSTALLOPT) -d $(INSTROOT)/lib/$(OS)/$(ARCH)
	./install.sh $(INSTROOT)/lib/$(OS)/$(ARCH) 755 *.so.*.*.*
	./install.sh $(INSTROOT)/lib/$(OS)/$(ARCH) 755 *.so.*
	./install.sh $(INSTROOT)/lib/$(OS)/$(ARCH) 755 *.so

depend:

clean distclean:
	rm -f *.a *.so.*.*.* *.so.* *.so
