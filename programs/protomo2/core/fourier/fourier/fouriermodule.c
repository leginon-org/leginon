/*----------------------------------------------------------------------------*
*
*  fouriermodule.c  -  fourier: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "fourier.h"
#include "exception.h"
#include "message.h"
#include "module.h"
#include "makedate.h"
#include <string.h>


/* exception messages */

static const ExceptionMessage FourierExceptions[ E_FOURIER_MAXCODE - E_FOURIER ] = {
  { "E_FOURIER",      "internal error ("FourierName")"            },
  { "E_FOURIER_INIT", "Fourier transform initialization failure"  },
  { "E_FOURIER_VERS", "unknown Fourier transform module/version"  },
  { "E_FOURIER_MODE", "invalid Fourier transform mode"            },
  { "E_FOURIER_TYPE", "invalid Fourier transform type"            },
  { "E_FOURIER_IMPL", "unimplemented Fourier transform algorithm" },
  { "E_FOURIER_DIM",  "unimplemented Fourier transform dimension" },
  { "E_FOURIER_SIZE", "invalid Fourier transform size"            },
};


/* module initialization/finalization */

static Status FourierPostModuleInit
              (void **data)

{
  Status status;

  /* default */
  status = FourierSet( FourierDefaultTransforms, True );
  if ( pushexception( status ) ) return status;

  if ( fourierdebug ) {
    char *ptr = FourierGet();
    if ( ptr != NULL ) {
      Message( "active: ", *ptr ? ptr : "none", "\n" ); free( ptr );
    }
  }

  return E_NONE;

}

static const Module FourierPostModule = {
  FourierName"-post",
  FourierVers,
  FourierCopy,
  COMPILE_DATE,
  FourierPostModuleInit,
  NULL,
  NULL,
};


#ifdef ENABLE_DYNAMIC

static const ModuleTable FourierTable[] = {
#ifdef ENABLE_FFTPACK
  { "lib"LIBPRFX"fftpack.so", "FFTpackModule", "fftpack" },
#endif
#ifdef ENABLE_FFTW2
  { "lib"LIBPRFX"fftw2.so",   "FFTW2Module",   "fftw2"   },
#endif
#ifdef ENABLE_GSLFFT
  { "lib"LIBPRFX"gslfft.so",  "GSLfftModule",  "gslfft"  },
#endif
#ifdef ENABLE_DJBFFT
  { "lib"LIBPRFX"djbfft.so",  "DJBfftModule",  "djbfft"  },
#endif
  { NULL,                      NULL,           "Fourier transform" }
};

#endif /* ENABLE_DYNAMIC */


static Status FourierModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( FourierExceptions, E_FOURIER, E_FOURIER_MAXCODE );
  if ( exception( status ) ) return status;

#ifdef ENABLE_DYNAMIC
  status = ModuleDynRegisterTable( FourierTable, FourierVers );
  if ( exception( status ) ) return status;
#endif /* ENABLE_DYNAMIC */

  status = ModuleRegister( &FourierPostModule );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module FourierModule = {
  FourierName,
  FourierVers,
  FourierCopy,
  COMPILE_DATE,
  FourierModuleInit,
  NULL,
  NULL,
};
