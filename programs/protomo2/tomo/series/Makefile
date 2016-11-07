#
# Makefile [series]
#
# Copyright © 2012 Hanspeter Winkler
#

#
# definitions
#

include   ../Makedefs

LIBMAJOR = 2

LIBMINOR = 1.0

PRFX = tomoseries

DIRS = config cache data series

EXTRADIRS = 

SOLIBS = -L../lib -l$(LIBPRFX)tomoio



#
# dependencies
#

cache: config

data: cache

series: cache


#
# common rules
#

include ../make/Makecommon
