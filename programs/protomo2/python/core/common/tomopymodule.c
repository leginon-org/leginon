/*----------------------------------------------------------------------------*
*
*  tomopymodule.c  -  tomopy: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomopy.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomoPyExceptions[ E_TOMOPY_MAXCODE - E_TOMOPY ] = {
  { "E_TOMOPY", "internal error ("TomoPyName")" },
};


/* module initialization/finalization */

static Status TomoPyModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomoPyExceptions, E_TOMOPY, E_TOMOPY_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomoPyModule = {
  TomoPyName,
  TomoPyVers,
  TomoPyCopy,
  COMPILE_DATE,
  TomoPyModuleInit,
  NULL,
  NULL,
};
