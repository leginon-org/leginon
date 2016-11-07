/*----------------------------------------------------------------------------*
*
*  windowmodule.c  -  window: image window
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "window.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage WindowExceptions[ E_WINDOW_MAXCODE - E_WINDOW ] = {
  { "E_WINDOW",      "internal error ("WindowName")" },
  { "E_WINDOW_AREA", "resampled area is too small"   },
};


/* module initialization/finalization */

static Status WindowModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( WindowExceptions, E_WINDOW, E_WINDOW_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module WindowModule = {
  WindowName,
  WindowVers,
  WindowCopy,
  COMPILE_DATE,
  WindowModuleInit,
  NULL,
  NULL,
};
