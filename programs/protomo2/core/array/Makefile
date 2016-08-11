#
# Makefile [array]
#
# Copyright © 2012 Hanspeter Winkler
#

#
# definitions
#

include ../Makedefs

LIBMAJOR = 2

LIBMINOR = 1.0

PRFX = array

DIRS = config array ccf convol linear mask polar preproc sample spatial \
       statistics transfer transform window

EXTRADIRS = 

SOLIBS = -L../lib -l$(LIBPRFX)core


#
# dependencies
#

array: config

ccf: config

convol: array

linear: transform

mask: array statistics

polar: transform

preproc: convol mask transfer spatial

sample: statistics transfer

spatial: array

statistics: config

transfer: config

transform: statistics transfer

window: linear mask


#
# common rules
#

include ../make/Makecommon
