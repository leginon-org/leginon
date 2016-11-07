/*----------------------------------------------------------------------------*
*
*  tomometamodule.c  -  series: tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomometa.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomometaExceptions[ E_TOMOMETA_MAXCODE - E_TOMOMETA ] = {
  { "E_TOMOMETA",     "internal error ("TomometaName")" },
  { "E_TOMOMETA_FMT", "invalid data file format"        },
};


/* module initialization/finalization */

static Status TomometaModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomometaExceptions, E_TOMOMETA, E_TOMOMETA_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomometaModule = {
  TomometaName,
  TomometaVers,
  TomometaCopy,
  COMPILE_DATE,
  TomometaModuleInit,
  NULL,
  NULL,
};
