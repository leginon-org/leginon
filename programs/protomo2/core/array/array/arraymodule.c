/*----------------------------------------------------------------------------*
*
*  arraymodule.c  -  array: array operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "array.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage ArrayExceptions[ E_ARRAY_MAXCODE - E_ARRAY ] = {
  { "E_ARRAY",        "internal error ("ArrayName")" },
  { "E_ARRAY_DIM",    "invalid array dimension"      },
  { "E_ARRAY_ZERO",   "zero length array"            },
  { "E_ARRAY_BOUNDS", "out of bounds"                },
};


/* module initialization/finalization */

static Status ArrayModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( ArrayExceptions, E_ARRAY, E_ARRAY_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module ArrayModule = {
  ArrayName,
  ArrayVers,
  ArrayCopy,
  COMPILE_DATE,
  ArrayModuleInit,
  NULL,
  NULL,
};
