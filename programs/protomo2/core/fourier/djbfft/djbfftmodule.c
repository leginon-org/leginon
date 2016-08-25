/*----------------------------------------------------------------------------*
*
*  djbfftmodule.c  -  djbfft: fast Fourier transforms
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "djbfft.h"
#include "djbfftcommon.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage DJBfftExceptions[ E_DJBFFT_MAXCODE - E_DJBFFT ] = {
  { "E_DJBFFT",      "internal error ("DJBfftName")"                         },
  { "E_DJBFFT_OPT",  "unimplemented Fourier transform option ("DJBfftName")" },
  { "E_DJBFFT_SIZE", "invalid Fourier transform size ("DJBfftName")"         },
};


/* meta data */

static const FourierVersion version = {
  "djb",
  { -1, 1, False, False },
  DJBfftInit,
  DJBfftFinal,
  {
    { /* forward */
      { DJBfftRealTransf,    DJBfftImagTransf,    DJBfftCmplxTransf    },
      { NULL,                NULL,                NULL                 },
      { NULL,                NULL,                NULL                 },
      { NULL,                NULL,                NULL                 },
      { NULL,                NULL,                NULL                 }
    },
    { /* backward */
      { DJBfftInvRealTransf, DJBfftInvImagTransf, DJBfftInvCmplxTransf },
      { NULL,                NULL,                NULL                 },
      { NULL,                NULL,                NULL                 },
      { NULL,                NULL,                NULL                 },
      { NULL,                NULL,                NULL                 }
    }
  }
};


/* module initialization/finalization */

static Status DJBfftModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( DJBfftExceptions, E_DJBFFT, E_DJBFFT_MAXCODE );
  if ( exception( status ) ) return status;

  status = FourierRegister( &version );
  if ( pushexception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module DJBfftModule = {
  DJBfftName,
  DJBfftVers,
  DJBfftCopy,
  COMPILE_DATE,
  DJBfftModuleInit,
  NULL,
  NULL,
};
