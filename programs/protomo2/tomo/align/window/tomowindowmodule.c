/*----------------------------------------------------------------------------*
*
*  tomowindowmodule.c  -  align: image windows
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomowindow.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomowindowExceptions[ E_TOMOWINDOW_MAXCODE - E_TOMOWINDOW ] = {
  { "E_TOMOWINDOW",      "internal error ("TomowindowName")" },
  { "E_TOMOWINDOW_SIZE", "invalid window size"               },
};


/* module initialization/finalization */

static Status TomowindowModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomowindowExceptions, E_TOMOWINDOW, E_TOMOWINDOW_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomowindowModule = {
  TomowindowName,
  TomowindowVers,
  TomowindowCopy,
  COMPILE_DATE,
  TomowindowModuleInit,
  NULL,
  NULL,
};
