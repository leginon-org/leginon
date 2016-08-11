/*----------------------------------------------------------------------------*
*
*  tomoseriesmapmodule.c  -  series: maps
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoseriesmap.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomoseriesmapExceptions[ E_TOMOSERIESMAP_MAXCODE - E_TOMOSERIESMAP ] = {
  { "E_TOMOSERIESMAP", "internal error ("TomoseriesmapName")" },
};


/* module initialization/finalization */

static Status TomoseriesmapModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomoseriesmapExceptions, E_TOMOSERIESMAP, E_TOMOSERIESMAP_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomoseriesmapModule = {
  TomoseriesmapName,
  TomoseriesmapVers,
  TomoseriesmapCopy,
  COMPILE_DATE,
  TomoseriesmapModuleInit,
  NULL,
  NULL,
};
