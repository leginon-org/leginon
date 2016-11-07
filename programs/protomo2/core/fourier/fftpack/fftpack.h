/*----------------------------------------------------------------------------*
*
*  fftpack.h  -  fftpack: fast Fourier transforms with fftpack
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef fftpack_h_
#define fftpack_h_

#include "fourier.h"

#define FFTpackName   "fftpack"
#define FFTpackVers   FourierVers
#define FFTpackCopy   FourierCopy


/* exception codes */

enum {
  E_FFTPACK = FFTpackModuleCode,
  E_FFTPACK_OPT,
  E_FFTPACK_SIZE,
  E_FFTPACK_MAXCODE
};


/* prototypes */

extern Status FFTpackRealTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count);

extern Status FFTpackRealEvenTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count);

extern Status FFTpackRealOddTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count);

extern Status FFTpackImagTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count);

extern Status FFTpackImagOddTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count);

extern Status FFTpackCmplxTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count);

extern Status FFTpackInvRealTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count);

extern Status FFTpackInvImagTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count);

extern Status FFTpackInvCmplxTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count);


#endif
