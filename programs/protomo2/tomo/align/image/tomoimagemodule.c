/*----------------------------------------------------------------------------*
*
*  tomoimagemodule.c  -  align: image geometry
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoimage.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomoimageExceptions[ E_TOMOIMAGE_MAXCODE - E_TOMOIMAGE ] = {
  { "E_TOMOIMAGE", "internal error ("TomoimageName")" },
};


/* module initialization/finalization */

static Status TomoimageModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomoimageExceptions, E_TOMOIMAGE, E_TOMOIMAGE_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomoimageModule = {
  TomoimageName,
  TomoimageVers,
  TomoimageCopy,
  COMPILE_DATE,
  TomoimageModuleInit,
  NULL,
  NULL,
};
