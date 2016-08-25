/*----------------------------------------------------------------------------*
*
*  fftpackmodule.c  -  fftpack: fast Fourier transforms with fftpack
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "fftpack.h"
#include "fftpackcommon.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage FFTpackExceptions[ E_FFTPACK_MAXCODE - E_FFTPACK ] = {
  { "E_FFTPACK",      "internal error ("FFTpackName")"                 },
  { "E_FFTPACK_OPT",  "unimplemented Fourier transform option ("FFTpackName")"  },
  { "E_FFTPACK_SIZE", "invalid Fourier transform size ("FFTpackName")" },
};


/* meta data */

static const FourierVersion version = {
  "fftpack",
  { -1, 1, False, False },
  FFTpackInit,
  FFTpackFinal,
  {
    { /* forward */
      { FFTpackRealTransf,     FFTpackImagTransf,     FFTpackCmplxTransf    },
      { FFTpackRealEvenTransf, FFTpackRealEvenTransf, NULL                  },
      { FFTpackRealOddTransf,  FFTpackImagOddTransf,  NULL                  },
      { NULL,                  NULL,                  NULL                  },
      { NULL,                  NULL,                  NULL                  }
    },
    { /* backward */
      { FFTpackInvRealTransf,  FFTpackInvImagTransf,  FFTpackInvCmplxTransf },
      { FFTpackRealEvenTransf, FFTpackRealEvenTransf, NULL                  },
      { FFTpackImagOddTransf,  FFTpackRealOddTransf,  NULL                  },
      { NULL,                  NULL,                  NULL                  },
      { NULL,                  NULL,                  NULL                  }
    }
  }
};


/* module initialization/finalization */

static Status FFTpackModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( FFTpackExceptions, E_FFTPACK, E_FFTPACK_MAXCODE );
  if ( exception( status ) ) return status;

  status = FourierRegister( &version );
  if ( pushexception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module FFTpackModule = {
  FFTpackName,
  FFTpackVers,
  FFTpackCopy,
  COMPILE_DATE,
  FFTpackModuleInit,
  NULL,
  NULL,
};
