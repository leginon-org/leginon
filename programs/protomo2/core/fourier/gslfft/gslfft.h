/*----------------------------------------------------------------------------*
*
*  gslfft.h  -  gslfft: fast Fourier transforms with gsl
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef gslfft_h_
#define gslfft_h_

#include "fourier.h"

#define GSLfftName   "gslfft"
#define GSLfftVers   FourierVers
#define GSLfftCopy   FourierCopy


/* exception codes */

enum {
  E_GSLFFT = GSLfftModuleCode,
  E_GSLFFT_OPT,
  E_GSLFFT_SIZE,
  E_GSLFFT_MAXCODE
};


/* prototypes */

extern Status GSLfftRealTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count);

extern Status GSLfftImagTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count);

extern Status GSLfftCmplxTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count);

extern Status GSLfftInvRealTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count);

extern Status GSLfftInvImagTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count);

extern Status GSLfftInvCmplxTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count);


#endif
