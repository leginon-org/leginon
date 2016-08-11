/*----------------------------------------------------------------------------*
*
*  tomogeommodule.c  -  tomography: tilt geometry
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomogeom.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomogeomExceptions[ E_TOMOGEOM_MAXCODE - E_TOMOGEOM ] = {
  { "E_TOMOGEOM",      "internal error ("TomogeomName")" },
  { "E_TOMOGEOM_AREA", "area out of bounds"              },
};


/* module initialization/finalization */

static Status TomogeomModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomogeomExceptions, E_TOMOGEOM, E_TOMOGEOM_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomogeomModule = {
  TomogeomName,
  TomogeomVers,
  TomogeomCopy,
  COMPILE_DATE,
  TomogeomModuleInit,
  NULL,
  NULL,
};
