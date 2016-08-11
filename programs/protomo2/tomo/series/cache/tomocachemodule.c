/*----------------------------------------------------------------------------*
*
*  tomocachemodule.c  -  series: image file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomocache.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomocacheExceptions[ E_TOMOCACHE_MAXCODE - E_TOMOCACHE ] = {
  { "E_TOMOCACHE",     "internal error ("TomocacheName")" },
  { "E_TOMOCACHE_FMT", "invalid data file format"         },
};


/* module initialization/finalization */

static Status TomocacheModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomocacheExceptions, E_TOMOCACHE, E_TOMOCACHE_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomocacheModule = {
  TomocacheName,
  TomocacheVers,
  TomocacheCopy,
  COMPILE_DATE,
  TomocacheModuleInit,
  NULL,
  NULL,
};
