#
# Makefile [everything]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# source directories
#

DIRS = align core fit fourier io map series seriesmap

EXTRADIRS = include lib bin


#
# make rules
#

.PHONY: help all libs install clean distclean depend
.PHONY: $(DIRS) $(EXTRADIRS)

help:
	@ echo "usage: make [ all | libs | install | depend | clean | distclean ]"

all libs: Makedate $(DIRS)

install: Makedate $(DIRS) $(EXTRADIRS)

clean: $(DIRS) $(EXTRADIRS)
	rm -f *.log

distclean: clean
	rm -f Makedate Makedefs make i3d

depend: Makedefs $(DIRS)
	@ date '+%Y%m%d%H%M' >Makedate

Makedate: Makedefs
	$(MAKE) depend

Makedefs:
	./configure.sh ../core


#
# descend into subdirectories
#

$(DIRS) $(EXTRADIRS):
	$(MAKE) -C $@ $(MAKECMDGOALS)


#
# dependencies
#

align: series

fit: core

fourier: series

io: core

map: io

series: io

seriesmap: series map
