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

PRFX = tomo

DIRS = config common geom param read tilt transfer

EXTRADIRS = 

SOLIBS = -L../i3d/lib -l$(LIBPRFX)imageio -l$(LIBPRFX)io -l$(LIBPRFX)image -l$(LIBPRFX)array -l$(LIBPRFX)core



#
# dependencies
#

common: config

geom: tilt

param: config

read: param

tilt: config

transfer: common


#
# common rules
#

include ../make/Makecommon
