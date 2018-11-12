/*----------------------------------------------------------------------------*
*
*  samplemodule.c  -  array: sampling
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "sample.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage SampleExceptions[ E_SAMPLE_MAXCODE - E_SAMPLE ] = {
  { "E_SAMPLE",          "internal error ("SampleName")"        },
  { "E_SAMPLE_DIM",      "invalid array dimension for sampling" },
  { "E_SAMPLE_DATATYPE", "invalid data type for sampling"       },
  { "E_SAMPLE_CLIP",     "sampling outside array bounds"        },
};


/* module initialization/finalization */

static Status SampleModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( SampleExceptions, E_SAMPLE, E_SAMPLE_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module SampleModule = {
  SampleName,
  SampleVers,
  SampleCopy,
  COMPILE_DATE,
  SampleModuleInit,
  NULL,
  NULL,
};
