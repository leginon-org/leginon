/*----------------------------------------------------------------------------*
*
*  tomodatamodule.c  -  series: image file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomodata.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomodataExceptions[ E_TOMODATA_MAXCODE - E_TOMODATA ] = {
  { "E_TOMODATA",      "internal error ("TomodataName")"        },
  { "E_TOMODATA_INDX", "invalid image index"                  },
  { "E_TOMODATA_DIM",  "invalid image dimension"              },
  { "E_TOMODATA_TYP",  "unimplemented data type"              },
  { "E_TOMODATA_SMP",  "data is undersampled"                 },
  { "E_TOMODATA_MOD",  "file was modified by another program" },
};


/* module initialization/finalization */

static Status TomodataModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomodataExceptions, E_TOMODATA, E_TOMODATA_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomodataModule = {
  TomodataName,
  TomodataVers,
  TomodataCopy,
  COMPILE_DATE,
  TomodataModuleInit,
  NULL,
  NULL,
};
