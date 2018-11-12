/*----------------------------------------------------------------------------*
*
*  matmodule.c  -  core: matrix operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "matdefs.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage MatExceptions[ E_MAT_MAXCODE - E_MAT ] = {
  { "E_MAT",     "internal error ("MatName")" },
  { "E_MATSING", "singular matrix"            },
};


/* module initialization/finalization */

static Status MatModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( MatExceptions, E_MAT, E_MAT_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module MatModule = {
  MatName,
  MatVers,
  MatCopy,
  COMPILE_DATE,
  MatModuleInit,
  NULL,
  NULL,
};
