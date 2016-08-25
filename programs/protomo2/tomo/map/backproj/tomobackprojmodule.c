/*----------------------------------------------------------------------------*
*
*  tomobackprojmodule.c  -  map: weighted backprojection
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomobackproj.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomobackprojExceptions[ E_TOMOBACKPROJ_MAXCODE - E_TOMOBACKPROJ ] = {
  { "E_TOMOBACKPROJ",      "internal error ("TomobackprojName")" },
  { "E_TOMOBACKPROJ_CLIP", "out of array bounds"                 },
};


/* module initialization/finalization */

static Status TomobackprojModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomobackprojExceptions, E_TOMOBACKPROJ, E_TOMOBACKPROJ_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomobackprojModule = {
  TomobackprojName,
  TomobackprojVers,
  TomobackprojCopy,
  COMPILE_DATE,
  TomobackprojModuleInit,
  NULL,
  NULL,
};
