/*----------------------------------------------------------------------------*
*
*  tomotransfermodule.c  -  tomography: transfer functions
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomotransfer.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomotransferExceptions[ E_TOMOTRANSFER_MAXCODE - E_TOMOTRANSFER ] = {
  { "E_TOMOTRANSFER", "internal error ("TomotransferName")" },
};


/* module initialization/finalization */

static Status TomotransferModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomotransferExceptions, E_TOMOTRANSFER, E_TOMOTRANSFER_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomotransferModule = {
  TomotransferName,
  TomotransferVers,
  TomotransferCopy,
  COMPILE_DATE,
  TomotransferModuleInit,
  NULL,
  NULL,
};
