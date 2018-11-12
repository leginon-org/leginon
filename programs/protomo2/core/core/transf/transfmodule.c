/*----------------------------------------------------------------------------*
*
*  transfmodule.c  -  core: linear transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "transfdefs.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TransfExceptions[ E_TRANSF_MAXCODE - E_TRANSF ] = {
  { "E_TRANSF",      "internal error ("TransfName")"  },
  { "E_TRANSF_SING", "singular transformation matrix" },
};


/* module initialization/finalization */

static Status TransfModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TransfExceptions, E_TRANSF, E_TRANSF_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module TransfModule = {
  TransfName,
  TransfVers,
  TransfCopy,
  COMPILE_DATE,
  TransfModuleInit,
  NULL,
  NULL,
};
