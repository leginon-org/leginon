/*----------------------------------------------------------------------------*
*
*  fftw2module.c  -  fftw2: fast Fourier transforms with fftw version 2
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "fftw2.h"
#include "fftw2common.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage FFTW2Exceptions[ E_FFTW2_MAXCODE - E_FFTW2 ] = {
  { "E_FFTW2",      "internal error ("FFTW2Name")"                           },
  { "E_FFTW2_INIT", "Fourier transform initialization failure ("FFTW2Name")" },
  { "E_FFTW2_OPT",  "unimplemented Fourier transform option ("FFTW2Name")"  },
  { "E_FFTW2_SIZE", "invalid Fourier transform size ("FFTW2Name")"           },
};


/* meta data */

static const FourierVersion version = {
  "fftw2",
  { -1, 1, False, False },
  FFTW2Init,
  FFTW2Final,
  {
    { /* forward */
      { FFTW2RealTransf,    NULL, FFTW2CmplxTransf    },
      { NULL,               NULL, NULL                },
      { NULL,               NULL, NULL                },
      { NULL,               NULL, NULL                },
      { NULL,               NULL, NULL                }
    },
    { /* backward */
      { FFTW2InvRealTransf, NULL, FFTW2InvCmplxTransf },
      { NULL,               NULL, NULL                },
      { NULL,               NULL, NULL                },
      { NULL,               NULL, NULL                },
      { NULL,               NULL, NULL                }
    }
  }
};


/* module initialization/finalization */

static Status FFTW2ModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( FFTW2Exceptions, E_FFTW2, E_FFTW2_MAXCODE );
  if ( exception( status ) ) return status;

  status = FourierRegister( &version );
  if ( pushexception( status ) ) return status;

#ifdef ENABLE_FFTW2_THREADS
  if ( fftw_threads_init() ) {
    return pushexception( E_FFTW2_INIT );
  }
#endif

  return E_NONE;

}


/* module descriptor */

const Module FFTW2Module = {
  FFTW2Name,
  FFTW2Vers,
  FFTW2Copy,
  COMPILE_DATE,
  FFTW2ModuleInit,
  NULL,
  NULL,
};
