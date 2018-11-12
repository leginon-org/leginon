/*----------------------------------------------------------------------------*
*
*  tomomodule.c  -  core: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomo.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomoExceptions[ E_TOMO_MAXCODE - E_TOMO ] = {
  { "E_TOMO", "internal error ("TomoName")" },
};


/* module initialization/finalization */

static Status TomoModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomoExceptions, E_TOMO, E_TOMO_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomoModule = {
  TomoName,
  TomoVers,
  TomoCopy,
  COMPILE_DATE,
  TomoModuleInit,
  NULL,
  NULL,
};
