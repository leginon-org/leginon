/*----------------------------------------------------------------------------*
*
*  i3iomodule.c  -  io: i3 input/output
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "i3io.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage I3ioExceptions[ E_I3IO_MAXCODE - E_I3IO ] = {
  { "E_I3IO",     "internal error ("I3ioName")" },
  { "E_I3IO_OFF", "invalid segment offset"      },
  { "E_I3IO_LEN", "invalid segment length"      },
};


/* module initialization/finalization */

static Status I3ioModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( I3ioExceptions, E_I3IO, E_I3IO_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module I3ioModule = {
  I3ioName,
  I3ioVers,
  I3ioCopy,
  COMPILE_DATE,
  I3ioModuleInit,
  NULL,
  NULL,
};
