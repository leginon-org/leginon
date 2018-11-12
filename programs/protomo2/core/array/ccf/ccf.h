/*----------------------------------------------------------------------------*
*
*  ccf.h  -  array: cross-correlation functions
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef ccf_h_
#define ccf_h_

#include "arraydefs.h"

#define CcfName   "ccf"
#define CcfVers   ARRAYVERS"."ARRAYBUILD
#define CcfCopy   ARRAYCOPY


/* exception codes */

enum {
  E_CCF = CcfModuleCode,
  E_CCF_MODE,
  E_CCF_TYPE,
  E_CCF_MAXCODE
};


/* types */

typedef enum {
  CC_UNDEF,
  CC_XCF,
  CC_MCF,
  CC_PCF,
  CC_DBL,
} CCMode;

typedef struct {
  CCMode mode;
  const char *ident;
} CcfParam;


/* constants */

#define CcfParamInitializer  (CcfParam){ CC_UNDEF, NULL }


/* prototypes */

extern Status CCF
              (Type type,
               Size count,
               const void *src0,
               const void *src1,
               void *dst,
               const CCMode mode);

extern Status CCFReal
              (Size count,
               const void *src0,
               const void *src1,
               void *dst,
               const CCMode mode);

extern Status CCFImag
              (Size count,
               const void *src0,
               const void *src1,
               void *dst,
               const CCMode mode);

extern Status CCFCmplx
              (Size count,
               const void *src0,
               const void *src1,
               void *dst,
               const CCMode mode);

extern Status CCFmod
              (Type type,
               Size count,
               void *dst,
               const CCMode mode);

extern Status CCFmodReal
              (Size count,
               void *dst,
               const CCMode mode);

extern Status CCFmodCmplx
              (Size count,
               void *dst,
               const CCMode mode);

extern Status CCFmodcalc
              (Type type,
               Size count,
               const void *src0,
               const void *src1,
               void *dst,
               const CCMode mode);

extern Status CCFmodcalcReal
              (Size count,
               const void *src0,
               const void *src1,
               void *dst,
               const CCMode mode);

extern Status CCFmodcalcCmplx
              (Size count,
               const void *src0,
               const void *src1,
               void *dst,
               const CCMode mode);

extern Status XCFReal
              (Size count,
               const Real *src0,
               const Real *src1,
               Real *dst);

extern Status XCFImag
              (Size count,
               const Imag *src0,
               const Imag *src1,
               Real *dst);

extern Status XCFCmplx
              (Size count,
               const Cmplx *src0,
               const Cmplx *src1,
               Cmplx *dst);

extern Status MCFReal
              (Size count,
               const Real *src0,
               const Real *src1,
               Real *dst);

extern Status MCFImag
              (Size count,
               const Imag *src0,
               const Imag *src1,
               Real *dst);

extern Status MCFCmplx
              (Size count,
               const Cmplx *src0,
               const Cmplx *src1,
               Cmplx *dst);

extern Status PCFReal
              (Size count,
               const Real *src0,
               const Real *src1,
               Real *dst);

extern Status PCFImag
              (Size count,
               const Imag *src0,
               const Imag *src1,
               Real *dst);

extern Status PCFCmplx
              (Size count,
               const Cmplx *src0,
               const Cmplx *src1,
               Cmplx *dst);

extern Status DBLReal
              (Size count,
               const Real *src0,
               const Real *src1,
               Real *dst);

extern Status DBLImag
              (Size count,
               const Imag *src0,
               const Imag *src1,
               Real *dst);

extern Status DBLCmplx
              (Size count,
               const Cmplx *src0,
               const Cmplx *src1,
               Cmplx *dst);

extern Status MCFmodReal
              (Size count,
               Real *dst);

extern Status MCFmodCmplx
              (Size count,
               Cmplx *dst);

extern Status PCFmodReal
              (Size count,
               Real *dst);

extern Status PCFmodCmplx
              (Size count,
               Cmplx *dst);


#endif
