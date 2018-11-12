/*----------------------------------------------------------------------------*
*
*  fftw2.h  -  fftw2: fast Fourier transforms with fftw version 2
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef fftw2_h_
#define fftw2_h_

#include "fourier.h"

#define FFTW2Name   "fftw2"
#define FFTW2Vers   FourierVers
#define FFTW2Copy   FourierCopy


/* exception codes */

enum {
  E_FFTW2 = FFTW2ModuleCode,
  E_FFTW2_INIT,
  E_FFTW2_OPT,
  E_FFTW2_SIZE,
  E_FFTW2_MAXCODE
};


/* prototypes */

extern Status FFTW2RealTransf
              (const Fourier *fou,
               const void *srcaddr,
               void *dstaddr,
               Size count);

extern Status FFTW2CmplxTransf
              (const Fourier *fou,
               const void *srcaddr,
               void *dstaddr,
               Size count);

extern Status FFTW2InvRealTransf
              (const Fourier *fou,
               const void *srcaddr,
               void *dstaddr,
               Size count);

extern Status FFTW2InvCmplxTransf
              (const Fourier *fou,
               const void *srcaddr,
               void *dstaddr,
               Size count);


#endif
