/*----------------------------------------------------------------------------*
*
*  windowfouriermodule.c  -  window: image windows
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "windowfourier.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage WindowFourierExceptions[ E_WINDOWFOURIER_MAXCODE - E_WINDOWFOURIER ] = {
  { "E_WINDOWFOURIER", "internal error ("WindowFourierName")" },
};


/* module initialization/finalization */

static Status WindowFourierModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( WindowFourierExceptions, E_WINDOWFOURIER, E_WINDOWFOURIER_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module WindowFourierModule = {
  WindowFourierName,
  WindowFourierVers,
  WindowFourierCopy,
  COMPILE_DATE,
  WindowFourierModuleInit,
  NULL,
  NULL,
};
