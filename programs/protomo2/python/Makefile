#
# Makefile [everything]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# source directories
#

DIRS = core modules

EXTRADIRS = include lib


#
# make rules
#

.PHONY: help all libs install clean distclean depend
.PHONY: $(DIRS) $(EXTRADIRS)

help:
	@ echo "usage: make [ all | install | depend | clean | distclean ]"

all libs: Makedate $(DIRS)

install: Makedate $(DIRS) $(EXTRADIRS)

clean: $(DIRS) $(EXTRADIRS)
	rm -f *.log

distclean: clean
	rm -f Makedate Makedefs make i3d i3dtomo i3dgui i3deman setup-py.sh

depend: Makedefs $(DIRS)
	@ date '+%Y%m%d%H%M' >Makedate

Makedate: Makedefs
	$(MAKE) depend

Makedefs:
	./configure.sh ../core ../tomo ../gui $(EMAN2DIR)


#
# descend into subdirectories
#

$(DIRS) $(EXTRADIRS):
	$(MAKE) -C $@ $(MAKECMDGOALS)


#
# dependencies
#

modules: core
