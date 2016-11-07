/*----------------------------------------------------------------------------*
*
*  tomodiagnmodule.c  -  align: diagnostic output
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomodiagn.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomodiagnExceptions[ E_TOMODIAGN_MAXCODE - E_TOMODIAGN ] = {
  { "E_TOMODIAGN", "internal error ("TomodiagnName")" },
};


/* module initialization/finalization */

static Status TomodiagnModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomodiagnExceptions, E_TOMODIAGN, E_TOMODIAGN_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomodiagnModule = {
  TomodiagnName,
  TomodiagnVers,
  TomodiagnCopy,
  COMPILE_DATE,
  TomodiagnModuleInit,
  NULL,
  NULL,
};
