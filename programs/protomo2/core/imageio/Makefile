#
# Makefile [imageio]
#
# Copyright © 2012 Hanspeter Winkler
#

#
# definitions
#

include ../Makedefs

LIBMAJOR = 2

LIBMINOR = 1.0

PRFX = imageio

LIBIMAGEIO = ccp4io emio imagicio spiderio suprimio tiffio

ifdef SO

  DIRS = config common extra fffio

  EXTRADIRS = $(LIBIMAGEIO)

else

  DIRS = config common extra fffio $(LIBIMAGEIO)

  EXTRADIRS =

endif

SOLIBS = -L../lib -l$(LIBPRFX)io -l$(LIBPRFX)image


#
# dependencies
#

common: config

ccp4io: common

emio: common

extra: common

fffio: common

imagicio: common

spiderio: common

suprimio: common

tiffio: common


#
# common rules
#

include ../make/Makecommon
