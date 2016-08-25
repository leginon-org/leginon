/*----------------------------------------------------------------------------*
*
*  tomotiltmodule.c  -  tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomotilt.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomotiltExceptions[ E_TOMOTILT_MAXCODE - E_TOMOTILT ] = {
  { "E_TOMOTILT",        "internal error ("TomotiltName")" },
  { "E_TOMOTILT_INT",    "invalid integer number"          },
  { "E_TOMOTILT_REAL",   "invalid real number"             },
  { "E_TOMOTILT_AXIS",   "undefined tilt axis"             },
  { "E_TOMOTILT_ORIENT", "undefined orientation"           },
  { "E_TOMOTILT_IMAGE",  "image is undefined"              },
  { "E_TOMOTILT_DEF",    "invalid parameter redefinition"  },
  { "E_TOMOTILT_REDEF",  "implicit parameter redefinition" },
  { "E_TOMOTILT_VAL"  ,  "invalid value"                   },
  { "E_TOMOTILT_FILE",   "undefined file name(s)"          },
  { "E_TOMOTILT_OFFS",   "invalid file specification"      },
  { "E_TOMOTILT_EMPTY",  "no images in series"             },
  { "E_TOMOTILT_EMPARAM","undefined EM parameter(s)"       },
  { "E_TOMOTILT_PIXEL",  "pixel size is undefined"         },
  { "E_TOMOTILT_DEFOC",  "undefined defocus"               },
  { "E_TOMOTILT_THETA",  "undefined tilt angle(s)"         },
  { "E_TOMOTILT_ORIGIN", "undefined origin(s)"             },
  { "E_TOMOTILT_PARSE",  "parse error"                     },
};


/* module initialization/finalization */

static Status TomotiltModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomotiltExceptions, E_TOMOTILT, E_TOMOTILT_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomotiltModule = {
  TomotiltName,
  TomotiltVers,
  TomotiltCopy,
  COMPILE_DATE,
  TomotiltModuleInit,
  NULL,
  NULL,
};
