#
# Makefile [align]
#
# Copyright © 2012 Hanspeter Winkler
#

#
# definitions
#

include   ../Makedefs

LIBMAJOR = 2

LIBMINOR = 1.0

PRFX = tomoalign

DIRS = config align diagnostic image reference window

EXTRADIRS = 

SOLIBS = -L../lib -l$(LIBPRFX)tomoseries



#
# dependencies
#

align: diagnostic reference window

diagnostic: config

image: config

window: config

reference: image


#
# common rules
#

include ../make/Makecommon
