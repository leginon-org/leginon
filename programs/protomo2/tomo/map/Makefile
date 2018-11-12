#
# Makefile [map]
#
# Copyright © 2012 Hanspeter Winkler
#

#
# definitions
#

include   ../Makedefs

LIBMAJOR = 2

LIBMINOR = 1.0

PRFX = tomomap

DIRS = config backproj common

EXTRADIRS = 

SOLIBS = -L../lib -l$(LIBPRFX)tomoio



#
# dependencies
#

backproj: config

common: backproj


#
# common rules
#

include ../make/Makecommon
