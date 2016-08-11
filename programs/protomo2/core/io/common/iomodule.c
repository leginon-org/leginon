/*----------------------------------------------------------------------------*
*
*  iomodule.c  -  io: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "io.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage IOExceptions[ E_IO_MAXCODE - E_IO ] = {
  { "E_IO",     "internal error ("IOName")" },
  { "E_IO_DIR", "cannot create directory"   },
};


/* module initialization/finalization */

static Status IOModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( IOExceptions, E_IO, E_IO_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module IOModule = {
  IOName,
  IOVers,
  IOCopy,
  COMPILE_DATE,
  IOModuleInit,
  NULL,
  NULL,
};
