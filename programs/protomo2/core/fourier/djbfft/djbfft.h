/*----------------------------------------------------------------------------*
*
*  djbfft.h  -  djbfft: fast Fourier transforms
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef djbfft_h_
#define djbfft_h_

#include "fourier.h"

#define DJBfftName   "djbfft"
#define DJBfftVers   FourierVers
#define DJBfftCopy   FourierCopy


/* exception codes */

enum {
  E_DJBFFT = DJBfftModuleCode,
  E_DJBFFT_OPT,
  E_DJBFFT_SIZE,
  E_DJBFFT_MAXCODE
};


/* prototypes */

extern Status DJBfftRealTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count);

extern Status DJBfftImagTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count);

extern Status DJBfftCmplxTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count);

extern Status DJBfftInvRealTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count);

extern Status DJBfftInvImagTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count);

extern Status DJBfftInvCmplxTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count);


#endif
