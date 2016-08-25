/*----------------------------------------------------------------------------*
*
*  preprocmodule.c  -  image: preprocessing
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "preproc.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage PreprocExceptions[ E_PREPROC_MAXCODE - E_PREPROC ] = {
  { "E_PREPROC",      "internal error ("PreprocName")" },
  { "E_PREPROC_DIM",  "unsupported array dimension for preprocessing" },
  { "E_PREPROC_TYPE", "invalid data type for preprocessing" },
};


/* module initialization/finalization */

static Status PreprocModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( PreprocExceptions, E_PREPROC, E_PREPROC_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module PreprocModule = {
  PreprocName,
  PreprocVers,
  PreprocCopy,
  COMPILE_DATE,
  PreprocModuleInit,
  NULL,
  NULL,
};
