#
# Makefile [core]
#
# Copyright © 2012 Hanspeter Winkler
#

#
# definitions
#

include   ../Makedefs

LIBMAJOR = 2

LIBMINOR = 1.0

PRFX = tomopy

DIRS = config common image

EXTRADIRS = gtk

ifdef EMAN2DIR
  EXTRADIRS += eman
endif

SOLIBS =



#
# dependencies
#

common: config

eman: image

gtk: image

image: common


#
# common rules
#

include ../make/Makecommon
