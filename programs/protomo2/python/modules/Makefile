#
# Makefile [modules]
#
# Copyright © 2012 Hanspeter Winkler
#

#
# definitions
#

include ../Makedefs

DIRS = protomo


#
# make rules
#

.PHONY: help all install clean distclean depend
.PHONY: $(DIRS)

help:
	@ echo "usage: make [ all | install | depend | clean | distclean ]"

all install: $(DIRS)

depend: $(DIRS)

clean distclean: $(DIRS)


#
# descend into subdirectories
#

$(DIRS):
	$(MAKE) -C $@ $(MAKECMDGOALS)
