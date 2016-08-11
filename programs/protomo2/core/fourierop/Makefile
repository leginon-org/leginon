#
# Makefile [fourierop]
#
# Copyright © 2012 Hanspeter Winkler
#

#
# definitions
#

include   ../Makedefs

LIBMAJOR = 2

LIBMINOR = 1.0

PRFX = fourierop

DIRS = config align fourier window

EXTRADIRS = 

SOLIBS = -L../lib -l$(LIBPRFX)image -l$(LIBPRFX)fourier



#
# dependencies
#

align: corr

corr: window

fourier: config

window: config


#
# common rules
#

include ../make/Makecommon
