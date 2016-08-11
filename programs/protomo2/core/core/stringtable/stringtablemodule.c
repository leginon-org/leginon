/*----------------------------------------------------------------------------*
*
*  stringtablemodule.c  -  core: character string table
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "stringtable.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage StringTableExceptions[ E_STRINGTABLE_MAXCODE - E_STRINGTABLE ] = {
  { "E_STRINGTABLE",          "internal error ("StringTableName")" },
  { "E_STRINGTABLE_NOTFOUND", "string not found"                   },
  { "E_STRINGTABLE_EXISTS",   "string already exists"              },
};


/* module initialization/finalization */

static Status StringTableModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( StringTableExceptions, E_STRINGTABLE, E_STRINGTABLE_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module StringTableModule = {
  StringTableName,
  StringTableVers,
  StringTableCopy,
  COMPILE_DATE,
  StringTableModuleInit,
  NULL,
  NULL,
};
