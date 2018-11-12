/*----------------------------------------------------------------------------*
*
*  tomorefmodule.c  -  align: reference
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoref.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomorefExceptions[ E_TOMOREF_MAXCODE - E_TOMOREF ] = {
  { "E_TOMOREF",      "internal error ("TomorefName")" },
  { "E_TOMOREF_TYPE", "invalid reference type"         },
  { "E_TOMOREF_ZERO", "empty reference"                },
};


/* module initialization/finalization */

static Status TomorefModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomorefExceptions, E_TOMOREF, E_TOMOREF_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomorefModule = {
  TomorefName,
  TomorefVers,
  TomorefCopy,
  COMPILE_DATE,
  TomorefModuleInit,
  NULL,
  NULL,
};
