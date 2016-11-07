/*----------------------------------------------------------------------------*
*
*  imageioextramodule.c  -  imageioextra: image files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imageioextra.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage ImageioExtraExceptions[ E_IMAGEIOEXTRA_MAXCODE - E_IMAGEIOEXTRA ] = {
  { "E_IMAGEIOEXTRA",      "internal error ("ImageioExtraName")" },
  { "E_IMAGEIOEXTRA_IMPL", "unimplemented i/o operation"         },
};


/* module initialization/finalization */

static Status ImageioExtraModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( ImageioExtraExceptions, E_IMAGEIOEXTRA, E_IMAGEIOEXTRA_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module ImageioExtraModule = {
  ImageioExtraName,
  ImageioExtraVers,
  ImageioExtraCopy,
  COMPILE_DATE,
  ImageioExtraModuleInit,
  NULL,
  NULL,
};
