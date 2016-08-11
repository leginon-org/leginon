/*----------------------------------------------------------------------------*
*
*  transformmodule.c  -  array: spatial transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "transform.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TransformExceptions[ E_TRANSFORM_MAXCODE - E_TRANSFORM ] = {
  { "E_TRANSFORM",      "internal error ("TransformName")" },
  { "E_TRANSFORM_CLIP", "out of array bounds"              },
};


/* module initialization/finalization */

static Status TransformModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TransformExceptions, E_TRANSFORM, E_TRANSFORM_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module TransformModule = {
  TransformName,
  TransformVers,
  TransformCopy,
  COMPILE_DATE,
  TransformModuleInit,
  NULL,
  NULL,
};
