/*----------------------------------------------------------------------------*
*
*  imagestatmodule.c  -  image: statistics
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagestat.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage ImageStatExceptions[ E_IMAGESTAT_MAXCODE - E_IMAGESTAT ] = {
  { "E_IMAGESTAT", "internal error ("ImageStatName")" },
};


/* module initialization/finalization */

static Status ImageStatModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( ImageStatExceptions, E_IMAGESTAT, E_IMAGESTAT_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module ImageStatModule = {
  ImageStatName,
  ImageStatVers,
  ImageStatCopy,
  COMPILE_DATE,
  ImageStatModuleInit,
  NULL,
  NULL,
};
