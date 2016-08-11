/*----------------------------------------------------------------------------*
*
*  stringsmodule.c  -  core: character string operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "strings.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage StringsExceptions[ E_STRINGS_MAXCODE - E_STRINGS ] = {
  { "E_STRINGS", "internal error ("StringsName")" },
};


/* module initialization/finalization */

static Status StringsModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( StringsExceptions, E_STRINGS, E_STRINGS_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module StringsModule = {
  StringsName,
  StringsVers,
  StringsCopy,
  COMPILE_DATE,
  StringsModuleInit,
  NULL,
  NULL,
};
