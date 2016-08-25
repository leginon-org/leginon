#
# Makefile [everything]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# source directories
#

DIRS = approx array core fourier fourierop image imageio io

EXTRADIRS = include lib bin


#
# make rules
#

.PHONY: help all libs install clean distclean makeclean depend
.PHONY: $(DIRS) $(EXTRADIRS)

help:
	@ echo "usage: make [ all | libs | install | depend | clean | distclean ]"

all libs: Makedate $(DIRS)

install: Makedate $(DIRS) $(EXTRADIRS)

clean: $(DIRS) $(EXTRADIRS)
	rm -f *.log

distclean: makeclean clean
	rm -f Makedate Makedefs config.h

makeclean:
	@ touch Makedefs

depend: Makedefs $(DIRS)
	@ date '+%Y%m%d%H%M' >Makedate

Makedate: Makedefs
	$(MAKE) depend

Makedefs:
	./configure.sh inst=$(INSTROOT) libs=$(DEPLIBS) $(OPTIONS)


#
# descend into subdirectories
#

$(DIRS) $(EXTRADIRS):
	$(MAKE) -C $@ $(MAKECMDGOALS)


#
# dependencies
#

approx: core

array: core

fourier: core

fourierop: fourier image

image: array

imageio: image io

io: core
