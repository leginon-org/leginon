/*----------------------------------------------------------------------------*
*
*  stringformatmodule.c  -  core: character string operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "stringformat.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage StringFormatExceptions[ E_STRINGFORMAT_MAXCODE - E_STRINGFORMAT ] = {
  { "E_STRINGFORMAT", "internal error ("StringFormatName")" },
};


/* module initialization/finalization */

static Status StringFormatModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( StringFormatExceptions, E_STRINGFORMAT, E_STRINGFORMAT_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module StringFormatModule = {
  StringFormatName,
  StringFormatVers,
  StringFormatCopy,
  COMPILE_DATE,
  StringFormatModuleInit,
  NULL,
  NULL,
};
