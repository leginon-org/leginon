/*----------------------------------------------------------------------------*
*
*  maskmodule.c  -  array: mask operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "mask.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage MaskExceptions[ E_MASK_MAXCODE - E_MASK ] = {
  { "E_MASK",      "internal error ("MaskName")"          },
  { "E_MASK_DIM",  "unsupported array dimension for mask" },
  { "E_MASK_TYPE", "unsupported data type for mask"       },
  { "E_MASK_MODE", "unsupported mask mode"                },
  { "E_MASK_FUNC", "unsupported mask function"            },
};


/* module initialization/finalization */

static Status MaskModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( MaskExceptions, E_MASK, E_MASK_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module MaskModule = {
  MaskName,
  MaskVers,
  MaskCopy,
  COMPILE_DATE,
  MaskModuleInit,
  NULL,
  NULL,
};
