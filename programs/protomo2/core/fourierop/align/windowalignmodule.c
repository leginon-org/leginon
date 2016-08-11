/*----------------------------------------------------------------------------*
*
*  windowalignmodule.c  -  fourierop: window alignment
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "windowalign.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage WindowAlignExceptions[ E_WINDOWALIGN_MAXCODE - E_WINDOWALIGN ] = {
  { "E_WINDOWALIGN", "internal error ("WindowAlignName")" },
};


/* module initialization/finalization */

static Status WindowAlignModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( WindowAlignExceptions, E_WINDOWALIGN, E_WINDOWALIGN_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module WindowAlignModule = {
  WindowAlignName,
  WindowAlignVers,
  WindowAlignCopy,
  COMPILE_DATE,
  WindowAlignModuleInit,
  NULL,
  NULL,
};
