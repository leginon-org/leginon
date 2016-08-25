#
# Makefile [io]
#
# Copyright © 2012 Hanspeter Winkler
#

#
# definitions
#

include ../Makedefs

LIBMAJOR = 2

LIBMINOR = 1.0

PRFX = io

DIRS = config common data fileio heap i3io proc textio

EXTRADIRS = 

SOLIBS = -L../lib -l$(LIBPRFX)core


#
# dependencies
#

common: config

data: config

fileio: common

heap: config

i3io: proc

proc: fileio heap

textio: common


#
# common rules
#

include ../make/Makecommon
