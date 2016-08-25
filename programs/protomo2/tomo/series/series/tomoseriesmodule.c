/*----------------------------------------------------------------------------*
*
*  tomoseriesmodule.c  -  series: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoseries.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomoseriesExceptions[ E_TOMOSERIES_MAXCODE - E_TOMOSERIES ] = {
  { "E_TOMOSERIES",      "internal error ("TomoseriesName")" },
  { "E_TOMOSERIES_SMP",  "invalid sampling factor"           },
  { "E_TOMOSERIES_ALI",  "unaligned image(s)"                },
  { "E_TOMOSERIES_VOL",  "volume is zero"                    },
};


/* module initialization/finalization */

static Status TomoseriesModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomoseriesExceptions, E_TOMOSERIES, E_TOMOSERIES_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomoseriesModule = {
  TomoseriesName,
  TomoseriesVers,
  TomoseriesCopy,
  COMPILE_DATE,
  TomoseriesModuleInit,
  NULL,
  NULL,
};
