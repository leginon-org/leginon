/*----------------------------------------------------------------------------*
*
*  textiomodule.c  -  io: text file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "textio.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TextioExceptions[ E_TEXTIO_MAXCODE - E_TEXTIO ] = {
  { "E_TEXTIO",      "internal error ("TextioName")" },
  { "E_TEXTIO_READ", "text file read error"          },
};


/* module initialization/finalization */

static Status TextioModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TextioExceptions, E_TEXTIO, E_TEXTIO_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module TextioModule = {
  TextioName,
  TextioVers,
  TextioCopy,
  COMPILE_DATE,
  TextioModuleInit,
  NULL,
  NULL,
};
