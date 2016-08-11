/*----------------------------------------------------------------------------*
*
*  linearmodule.c  -  array: spatial linear transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "linear.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage LinearExceptions[ E_LINEAR_MAXCODE - E_LINEAR ] = {
  { "E_LINEAR",          "internal error ("LinearName")"             },
  { "E_LINEAR_DIM",      "invalid array dimension for interpolation" },
  { "E_LINEAR_DATATYPE", "invalid data type for interpolation"       },
};


/* module initialization/finalization */

static Status LinearModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( LinearExceptions, E_LINEAR, E_LINEAR_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module LinearModule = {
  LinearName,
  LinearVers,
  LinearCopy,
  COMPILE_DATE,
  LinearModuleInit,
  NULL,
  NULL,
};
