/*----------------------------------------------------------------------------*
*
*  nmminmodule.c  -  approx: Nelder Mead minimization
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "nmmin.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage NMminExceptions[ E_NMMIN_MAXCODE - E_NMMIN ] = {
  { "E_NMMIN",       "internal error ("NMminName")"  },
  { "E_NMMIN_FAIL",  "Nelder Mead minimization failed" },
};


/* module initialization/finalization */

static Status NMminModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( NMminExceptions, E_NMMIN, E_NMMIN_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module NMminModule = {
  NMminName,
  NMminVers,
  NMminCopy,
  COMPILE_DATE,
  NMminModuleInit,
  NULL,
  NULL,
};
