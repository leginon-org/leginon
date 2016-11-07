/*----------------------------------------------------------------------------*
*
*  spatialmodule.c  -  array: spatial operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "spatial.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage SpatialExceptions[ E_SPATIAL_MAXCODE - E_SPATIAL ] = {
  { "E_SPATIAL",      "internal error ("SpatialName")" },
  { "E_SPATIAL_PEAK", "peak search error"              },
};


/* module initialization/finalization */

static Status SpatialModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( SpatialExceptions, E_SPATIAL, E_SPATIAL_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module SpatialModule = {
  SpatialName,
  SpatialVers,
  SpatialCopy,
  COMPILE_DATE,
  SpatialModuleInit,
  NULL,
  NULL,
};
