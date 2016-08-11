/*----------------------------------------------------------------------------*
*
*  tomoalignmodule.c  -  align: series alignment
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoalign.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomoalignExceptions[ E_TOMOALIGN_MAXCODE - E_TOMOALIGN ] = {
  { "E_TOMOALIGN",     "internal error ("TomoalignName")" },
  { "E_TOMOALIGN_RNG", "invalid image range"              },
};


/* module initialization/finalization */

static Status TomoalignModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomoalignExceptions, E_TOMOALIGN, E_TOMOALIGN_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomoalignModule = {
  TomoalignName,
  TomoalignVers,
  TomoalignCopy,
  COMPILE_DATE,
  TomoalignModuleInit,
  NULL,
  NULL,
};
