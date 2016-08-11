#
# Makefile [io]
#
# Copyright © 2012 Hanspeter Winkler
#

#
# definitions
#

include   ../Makedefs

LIBMAJOR = 2

LIBMINOR = 1.0

PRFX = tomoio

DIRS = config common file meta

EXTRADIRS = 

SOLIBS = -L../lib -l$(LIBPRFX)tomo



#
# dependencies
#

common: meta

file: config

meta: file


#
# common rules
#

include ../make/Makecommon
