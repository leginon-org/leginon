#
# Makefile [image]
#
# Copyright © 2012 Hanspeter Winkler
#

#
# definitions
#

include ../Makedefs

LIBMAJOR = 2

LIBMINOR = 1.0

PRFX = image

DIRS = config array common ctf mask statistics

EXTRADIRS = 

SOLIBS = -L../lib -l$(LIBPRFX)array


#
# dependencies
#

array: common

common: config

ctf: common

mask: common

statistics: array


#
# common rules
#

include ../make/Makecommon
