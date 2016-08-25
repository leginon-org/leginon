/*----------------------------------------------------------------------------*
*
*  polarmodule.c  -  array: spatial polar transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "polar.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage PolarExceptions[ E_POLAR_MAXCODE - E_POLAR ] = {
  { "E_POLAR",          "internal error ("PolarName")"              },
  { "E_POLAR_DIM",      "invalid array dimension for interpolation" },
  { "E_POLAR_DATATYPE", "invalid data type for interpolation"       },
};


/* module initialization/finalization */

static Status PolarModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( PolarExceptions, E_POLAR, E_POLAR_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module PolarModule = {
  PolarName,
  PolarVers,
  PolarCopy,
  COMPILE_DATE,
  PolarModuleInit,
  NULL,
  NULL,
};
