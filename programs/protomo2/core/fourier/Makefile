#
# Makefile [fourier]
#
# Copyright © 2012 Hanspeter Winkler
#

#
# definitions
#

include ../Makedefs

LIBMAJOR = 2

LIBMINOR = 1.0

PRFX = fourier

ifdef LIBFFTPACK
  LIBFFT += fftpack
endif
ifdef LIBFFTW2
  LIBFFT += fftw2
endif
ifdef LIBDJBFFT
  LIBFFT += djbfft
endif
ifdef LIBGSLFFT
  LIBFFT += gslfft
endif

ifdef SO

  DIRS = config fourier

  EXTRADIRS = $(LIBFFT)

else

  DIRS = config fourier $(LIBFFT)

  EXTRADIRS =

endif

SOLIBS = -L../lib -l$(LIBPRFX)core


#
# dependencies
#

fourier: config

djbfft: fourier

fftpack: fourier

fftw2: fourier

gslfft: fourier


#
# common rules
#

include ../make/Makecommon
