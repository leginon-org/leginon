/*----------------------------------------------------------------------------*
*
*  gslfftmodule.c  -  gslfft: fast Fourier transforms with gsl
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "gslfft.h"
#include "gslfftcommon.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage GSLfftExceptions[ E_GSLFFT_MAXCODE - E_GSLFFT ] = {
  { "E_GSLFFT",      "internal error ("GSLfftName")"                 },
  { "E_GSLFFT_OPT",  "unimplemented Fourier transform option ("GSLfftName")"  },
  { "E_GSLFFT_SIZE", "invalid Fourier transform size ("GSLfftName")" },
};


/* meta data */

static const FourierVersion version = {
  "gsl",
  { -1, 1, False, False },
  GSLfftInit,
  GSLfftFinal,
  {
    { /* forward */
      { GSLfftRealTransf,    GSLfftImagTransf,    GSLfftCmplxTransf    },
      { NULL,                NULL,                NULL                 },
      { NULL,                NULL,                NULL                 },
      { NULL,                NULL,                NULL                 },
      { NULL,                NULL,                NULL                 }
    },
    { /* backward */
      { GSLfftInvRealTransf, GSLfftInvImagTransf, GSLfftInvCmplxTransf },
      { NULL,                NULL,                NULL                 },
      { NULL,                NULL,                NULL                 },
      { NULL,                NULL,                NULL                 },
      { NULL,                NULL,                NULL                 }
    }
  }
};


/* module initialization/finalization */

static Status GSLfftModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( GSLfftExceptions, E_GSLFFT, E_GSLFFT_MAXCODE );
  if ( exception( status ) ) return status;

  status = FourierRegister( &version );
  if ( pushexception( status ) ) return status;

  gsl_set_error_handler_off();

  return E_NONE;

}


/* module descriptor */

const Module GSLfftModule = {
  GSLfftName,
  GSLfftVers,
  GSLfftCopy,
  COMPILE_DATE,
  GSLfftModuleInit,
  NULL,
  NULL,
};
