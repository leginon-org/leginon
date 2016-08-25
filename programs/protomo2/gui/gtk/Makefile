#
# Makefile [gtk]
#
# Copyright © 2012 Hanspeter Winkler
#

#
# definitions
#

include   ../Makedefs

LIBMAJOR = 2

LIBMINOR = 1.0

PRFX = gtk

DIRS = config common display

EXTRADIRS = 

SOLIBS = -L../lib -l$(LIBPRFX)gui



#
# dependencies
#

common: config

display: common


#
# common rules
#

include ../make/Makecommon
