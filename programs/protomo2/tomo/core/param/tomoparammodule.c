/*----------------------------------------------------------------------------*
*
*  tomoparammodule.c  -  tomography: parameter files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoparam.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomoparamExceptions[ E_TOMOPARAM_MAXCODE - E_TOMOPARAM ] = {
  { "E_TOMOPARAM",        "internal error ("TomoparamName")" },
  { "E_TOMOPARAM_OPSEC",  "section has no closing brace",    },
  { "E_TOMOPARAM_UNSEC",  "undefined section",               },
  { "E_TOMOPARAM_UNDEF",  "undefined parameter"              },
  { "E_TOMOPARAM_UINT",   "integer conversion error"         },
  { "E_TOMOPARAM_REAL",   "floating point conversion error"  },
  { "E_TOMOPARAM_IDENT",  "undefined identifier"             },
  { "E_TOMOPARAM_EXISTS", "identifier already defined"       },
  { "E_TOMOPARAM_OPERAT", "invalid operator"                 },
  { "E_TOMOPARAM_OPER",   "invalid operand"                  },
  { "E_TOMOPARAM_TYPE",   "incompatible data types"          },
  { "E_TOMOPARAM_DAT",    "invalid data type"                },
  { "E_TOMOPARAM_DIM",    "invalid dimension"                },
  { "E_TOMOPARAM_LEN",    "incompatible array size"          },
  { "E_TOMOPARAM_MAT",    "invalid matrix size"              },
  { "E_TOMOPARAM_SEL",    "invalid selection"                },
};


/* module initialization/finalization */

static Status TomoparamModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomoparamExceptions, E_TOMOPARAM, E_TOMOPARAM_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomoparamModule = {
  TomoparamName,
  TomoparamVers,
  TomoparamCopy,
  COMPILE_DATE,
  TomoparamModuleInit,
  NULL,
  NULL,
};
