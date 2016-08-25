/*----------------------------------------------------------------------------*
*
*  tomofilemodule.c  -  series: tilt series image file handling
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomofile.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomofileExceptions[ E_TOMOFILE_MAXCODE - E_TOMOFILE ] = {
  { "E_TOMOFILE",      "internal error ("TomofileName")"            },
  { "E_TOMOFILE_OPEN", "error opening image file(s)"                },
  { "E_TOMOFILE_DIM",  "invalid image dimension"                    },
  { "E_TOMOFILE_MOD",  "image file was modified by another program" },
};


/* module initialization/finalization */

static Status TomofileModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomofileExceptions, E_TOMOFILE, E_TOMOFILE_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomofileModule = {
  TomofileName,
  TomofileVers,
  TomofileCopy,
  COMPILE_DATE,
  TomofileModuleInit,
  NULL,
  NULL,
};
