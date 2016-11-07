/*----------------------------------------------------------------------------*
*
*  tomoiomodule.c  -  core: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoio.h"
#include "i3data.h"
#include "fileio.h"
#include "io.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomoioExceptions[ E_TOMOIO_MAXCODE - E_TOMOIO ] = {
  { "E_TOMOIO",      "internal error ("TomoioName")" },
  { "E_TOMOIO_OP",   "invalid i/o operation"               },
  { "E_TOMOIO_DIM",  "invalid image dimension"             },
  { "E_TOMOIO_META", "invalid meta data"                   },
  { "E_TOMOIO_REQ",  "required meta data has not been set" },
};


/* module initialization/finalization */

static Status TomoioModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomoioExceptions, E_TOMOIO, E_TOMOIO_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomoioModule = {
  TomoioName,
  TomoioVers,
  TomoioCopy,
  COMPILE_DATE,
  TomoioModuleInit,
  NULL,
  NULL,
};
