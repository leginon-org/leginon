/*----------------------------------------------------------------------------*
*
*  stringparsemodule.c  -  core: character string operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "stringparse.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage StringParseExceptions[ E_STRINGPARSE_MAXCODE - E_STRINGPARSE ] = {
  { "E_STRINGPARSE",           "internal error ("StringParseName")" },
  { "E_STRINGPARSE_ERROR",     "parse error"                        },
  { "E_STRINGPARSE_NOPARSE",   "nothing parsed"                     },
  { "E_STRINGPARSE_SEPAR",     "invalid separator"                  },
};


/* module initialization/finalization */

static Status StringParseModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( StringParseExceptions, E_STRINGPARSE, E_STRINGPARSE_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module StringParseModule = {
  StringParseName,
  StringParseVers,
  StringParseCopy,
  COMPILE_DATE,
  StringParseModuleInit,
  NULL,
  NULL,
};
