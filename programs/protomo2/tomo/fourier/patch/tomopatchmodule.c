/*----------------------------------------------------------------------------*
*
*  tomopatchmodule.c  -  fourier: patch
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomopatch.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomopatchExceptions[ E_TOMOPATCH_MAXCODE - E_TOMOPATCH ] = {
  { "E_TOMOPATCH", "internal error ("TomopatchName")" },
};


/* module initialization/finalization */

static Status TomopatchModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomopatchExceptions, E_TOMOPATCH, E_TOMOPATCH_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomopatchModule = {
  TomopatchName,
  TomopatchVers,
  TomopatchCopy,
  COMPILE_DATE,
  TomopatchModuleInit,
  NULL,
  NULL,
};
