/*----------------------------------------------------------------------------*
*
*  tomoparamreadmodule.c  -  core: retrieve parameters
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoparamread.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomoparamReadExceptions[ E_TOMOPARAMREAD_MAXCODE - E_TOMOPARAMREAD ] = {
  { "E_TOMOPARAMREAD",       "internal error ("TomoparamReadName")" },
  { "E_TOMOPARAMREAD_ERROR", "parameter read error"                 },
  { "E_TOMOPARAMREAD_SEC",   "invalid section"                      },
  { "E_TOMOPARAMREAD_PAR",   "invalid parameter"                    },
  { "E_TOMOPARAMREAD_VAL",   "invalid value"                        },
  { "E_TOMOPARAMREAD_CONFL", "parameter conflict"                   },
};


/* module initialization/finalization */

static Status TomoparamReadModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomoparamReadExceptions, E_TOMOPARAMREAD, E_TOMOPARAMREAD_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomoparamReadModule = {
  TomoparamReadName,
  TomoparamReadVers,
  TomoparamReadCopy,
  COMPILE_DATE,
  TomoparamReadModuleInit,
  NULL,
  NULL,
};
