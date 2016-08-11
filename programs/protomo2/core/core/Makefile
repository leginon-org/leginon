#
# Makefile [core]
#
# Copyright © 2012 Hanspeter Winkler
#

#
# definitions
#

include ../Makedefs

LIBMAJOR = 2

LIBMINOR = 1.0

PRFX = core

DIRS = config base checksum matrix parse sequence strings stringformat \
       stringparse stringtable thread transf

EXTRADIRS = 

SOLIBS =


#
# dependencies
#

base: config

checksum: config

matrix: base

parse: base

sequence: matrix

strings: base

stringformat: base

stringparse: base

stringtable: base

thread: base

transf: base


#
# common rules
#

include ../make/Makecommon
