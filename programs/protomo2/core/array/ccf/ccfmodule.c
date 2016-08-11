/*----------------------------------------------------------------------------*
*
*  ccfmodule.c  -  array: cross-correlation functions
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "ccf.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage CcfExceptions[ E_CCF_MAXCODE - E_CCF ] = {
  { "E_CCF",      "internal error ("CcfName")"              },
  { "E_CCF_MODE", "invalid cross-correlation mode"          },
  { "E_CCF_TYPE", "invalid data type for cross-correlation" },
};


/* module initialization/finalization */

static Status CcfModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( CcfExceptions, E_CCF, E_CCF_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module CcfModule = {
  CcfName,
  CcfVers,
  CcfCopy,
  COMPILE_DATE,
  CcfModuleInit,
  NULL,
  NULL,
};
