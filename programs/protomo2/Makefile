#
# Makefile [everything]
#
# Copyright © 2012 Hanspeter Winkler
#

#
# configuration options
#

include Makedefs


#
# source directories
#

DIRS = core tomo gui python


#
# make rules
#

.PHONY: help all libs install clean distclean instclean
.PHONY: $(DIRS)

help:
	@ echo "usage: make [ all | libs | install | clean | distclean | instclean ]"

all libs: $(DIRS)

install: $(DIRS)
	cat core/setup-i3d.sh python/setup-py.sh core/setup-sys.sh >setup.sh
	chmod +x setup.sh
	cp -p LICENSE VERSION setup.sh $(INSTROOT)

clean: $(DIRS)
	rm -f *.log

distclean: clean
	rm -f setup.sh

instclean:
	rm -rf $(INSTROOT)/lib  $(INSTROOT)/bin


#
# descend into subdirectories
#

$(DIRS):
	$(MAKE) -C $@ $(MAKECMDGOALS)


#
# dependencies
#

gui: tomo

python: gui

tomo: core
