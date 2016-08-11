#
# Makefile [inst]
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

.PHONY: help all install proginstall clean progclean distclean depend

help:
	@ echo "usage: make [ all | install | proginstall | depend | clean | progclean | distclean ]"

all:

install proginstall:
	$(INSTALL) $(INSTALLOPT) -d $(INSTROOT)/bin/$(OS)/$(ARCH)
ifdef MAINVERSION
	$(INSTALL) $(INSTALLOPT) -m 511 -t $(INSTROOT)/bin/$(OS)/$(ARCH) ../bin/*
endif

depend:

clean progclean distclean:
