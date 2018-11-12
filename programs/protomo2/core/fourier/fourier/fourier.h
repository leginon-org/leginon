/*----------------------------------------------------------------------------*
*
*  fourier.h  -  fourier: Fourier transforms
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef fourier_h_
#define fourier_h_

#include "fourierdefs.h"

#define FourierName   "fourier"
#define FourierVers   FOURIERVERS"."FOURIERBUILD
#define FourierCopy   FOURIERCOPY


/* exception codes */

enum {
  E_FOURIER = FourierModuleCode,
  E_FOURIER_INIT,
  E_FOURIER_VERS,
  E_FOURIER_MODE,
  E_FOURIER_TYPE,
  E_FOURIER_IMPL,
  E_FOURIER_DIM,
  E_FOURIER_SIZE,
  E_FOURIER_MAXCODE
};


/* types */

struct _Fourier;

typedef struct _Fourier Fourier;

typedef enum {
  FourierZeromean = 0x01,
  FourierUnscaled = 0x02,
  FourierSymUnctr = 0x04,
  FourierTrfUnctr = 0x08
} FourierOpt;


/* prototypes */

extern Status FourierSet
              (const char *ident,
               Bool optional);

extern char *FourierGet();

extern Fourier *FourierRealInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt);

extern Fourier *FourierRealEvenInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt);

extern Fourier *FourierRealOddInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt);

extern Fourier *FourierImagInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt);

extern Fourier *FourierImagEvenInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt);

extern Fourier *FourierImagOddInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt);

extern Fourier *FourierCmplxInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt);


extern Fourier *FourierInvRealInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt);

extern Fourier *FourierInvRealEvenInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt);

extern Fourier *FourierInvRealOddInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt);

extern Fourier *FourierInvImagInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt);

extern Fourier *FourierInvImagEvenInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt);

extern Fourier *FourierInvImagOddInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt);

extern Fourier *FourierInvCmplxInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt);


extern Status FourierRealTransf
              (const Fourier *fou,
               const Real *src,
               Cmplx *dst,
               Size count);

extern Status FourierRealEvenTransf
              (const Fourier *fou,
               const Real *src,
               Real *dst,
               Size count);

extern Status FourierRealOddTransf
              (const Fourier *fou,
               const Real *src,
               Imag *dst,
               Size count);

extern Status FourierImagTransf
              (const Fourier *fou,
               const Imag *src,
               Cmplx *dst,
               Size count);

extern Status FourierImagEvenTransf
              (const Fourier *fou,
               const Imag *src,
               Imag *dst,
               Size count);

extern Status FourierImagOddTransf
              (const Fourier *fou,
               const Imag *src,
               Real *dst,
               Size count);

extern Status FourierCmplxTransf
              (const Fourier *fou,
               const Cmplx *src,
               Cmplx *dst,
               Size count);


extern Status FourierInvRealTransf
              (const Fourier *fou,
               const Cmplx *src,
               Real *dst,
               Size count);

extern Status FourierInvRealEvenTransf
              (const Fourier *fou,
               const Real *src,
               Real *dst,
               Size count);

extern Status FourierInvRealOddTransf
              (const Fourier *fou,
               const Imag *src,
               Real *dst,
               Size count);

extern Status FourierInvImagTransf
              (const Fourier *fou,
               const Cmplx *src,
               Imag *dst,
               Size count);

extern Status FourierInvImagEvenTransf
              (const Fourier *fou,
               const Imag *src,
               Imag *dst,
               Size count);

extern Status FourierInvImagOddTransf
              (const Fourier *fou,
               const Real *src,
               Imag *dst,
               Size count);

extern Status FourierInvCmplxTransf
              (const Fourier *fou,
               const Cmplx *src,
               Cmplx *dst,
               Size count);


extern Status FourierTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count);

extern Status FourierFinal
              (Fourier *fou);


extern Status FourierReal
              (Size dim,
               const Size *len,
               const Real *src,
               Cmplx *dst,
               Size count,
               FourierOpt opt);

extern Status FourierRealEven
              (Size dim,
               const Size *len,
               const Real *src,
               Real *dst,
               Size count,
               FourierOpt opt);

extern Status FourierRealOdd
              (Size dim,
               const Size *len,
               const Real *src,
               Imag *dst,
               Size count,
               FourierOpt opt);

extern Status FourierImag
              (Size dim,
               const Size *len,
               const Imag *src,
               Cmplx *dst,
               Size count,
               FourierOpt opt);

extern Status FourierImagEven
              (Size dim,
               const Size *len,
               const Imag *src,
               Imag *dst,
               Size count,
               FourierOpt opt);

extern Status FourierImagOdd
              (Size dim,
               const Size *len,
               const Imag *src,
               Real *dst,
               Size count,
               FourierOpt opt);

extern Status FourierCmplx
              (Size dim,
               const Size *len,
               const Cmplx *src,
               Cmplx *dst,
               Size count,
               FourierOpt opt);


extern Status FourierInvReal
              (Size dim,
               const Size *len,
               const Cmplx *src,
               Real *dst,
               Size count,
               FourierOpt opt);

extern Status FourierInvRealEven
              (Size dim,
               const Size *len,
               const Real *src,
               Real *dst,
               Size count,
               FourierOpt opt);

extern Status FourierInvRealOdd
              (Size dim,
               const Size *len,
               const Imag *src,
               Real *dst,
               Size count,
               FourierOpt opt);

extern Status FourierInvImag
              (Size dim,
               const Size *len,
               const Cmplx *src,
               Imag *dst,
               Size count,
               FourierOpt opt);

extern Status FourierInvImagEven
              (Size dim,
               const Size *len,
               const Imag *src,
               Imag *dst,
               Size count,
               FourierOpt opt);

extern Status FourierInvImagOdd
              (Size dim,
               const Size *len,
               const Real *src,
               Imag *dst,
               Size count,
               FourierOpt opt);

extern Status FourierInvCmplx
              (Size dim,
               const Size *len,
               const Cmplx *src,
               Cmplx *dst,
               Size count,
               FourierOpt opt);


#endif
