/*----------------------------------------------------------------------------*
*
*  tomotiltfitmodule.c  -  tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomotiltfit.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomotiltFitExceptions[ E_TOMOTILTFIT_MAXCODE - E_TOMOTILTFIT ] = {
  { "E_TOMOTILTFIT",       "internal error ("TomoTiltFitName")"  },
  { "E_TOMOTILTFIT_NONE",  "no parameters are being fitted"      },
  { "E_TOMOTILTFIT_REF",   "invalid reference image for fitting" },
  { "E_TOMOTILTFIT_IMG",   "too few images to fit"               },
  { "E_TOMOTILTFIT_PARAM", "too many parameters"                 },
  { "E_TOMOTILTFIT_DATA",  "invalid data in function evaluation" },
  { "E_TOMOTILTFIT_FIT",   "geometry fitting error"              },
  { "E_TOMOTILTFIT_CORR",  "error while evaluating correction"   },
};


/* module initialization/finalization */

static Status TomotiltFitModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomotiltFitExceptions, E_TOMOTILTFIT, E_TOMOTILTFIT_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomotiltFitModule={
  TomoTiltFitName,
  TomoTiltFitVers,
  TomoTiltFitCopy,
  COMPILE_DATE,
  TomotiltFitModuleInit,
  NULL,
  NULL,
};
