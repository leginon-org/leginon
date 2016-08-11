/*----------------------------------------------------------------------------*
*
*  convolmodule.c  -  array: convolution type filters
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "convol.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage ConvolExceptions[ E_CONVOL_MAXCODE - E_CONVOL ] = {
  { "E_CONVOL",      "internal error ("ConvolName")" },
  { "E_CONVOL_SIZE", "array too small"               },
  { "E_CONVOL_TYPE", "invalid data type for filter"  },
};


/* module initialization/finalization */

static Status ConvolModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( ConvolExceptions, E_CONVOL, E_CONVOL_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module ConvolModule = {
  ConvolName,
  ConvolVers,
  ConvolCopy,
  COMPILE_DATE,
  ConvolModuleInit,
  NULL,
  NULL,
};
