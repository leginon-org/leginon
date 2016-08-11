/*----------------------------------------------------------------------------*
*
*  parsemodule.c  -  core: auxiliary parser routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "parse.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage ParseExceptions[ E_PARSE_MAXCODE - E_PARSE ] = {
  { "E_PARSE", "internal error ("ParseName")"  },
  { "E_PARSE_NO",     "nothing parsed"         },
  { "E_PARSE_EOF",    "premature EOF"          },
  { "E_PARSE_UNCOM",  "unterminated comment"   },
  { "E_PARSE_UNSTR",  "unterminated string"    },
  { "E_PARSE_UNCHR",  "unrecognized character" },
  { "E_PARSE_CTRCHR", "invalid character"      },
  { "E_PARSE_SYNTAX", "syntax error"           },
};


/* module initialization/finalization */

static Status ParseModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( ParseExceptions, E_PARSE, E_PARSE_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module ParseModule = {
  ParseName,
  ParseVers,
  ParseCopy,
  COMPILE_DATE,
  ParseModuleInit,
  NULL,
  NULL,
};
