/*----------------------------------------------------------------------------*
*
*  imagemaskmodule.c  -  image: mask operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagemask.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage ImageMaskExceptions[ E_IMAGEMASK_MAXCODE - E_IMAGEMASK ] = {
  { "E_IMAGEMASK",      "internal error ("ImageMaskName")"           },
  { "E_IMAGEMASK_DIM",  "unsupported array dimension for image mask" },
  { "E_IMAGEMASK_FUNC", "unsupported image mask function"            },
};


/* module initialization/finalization */

static Status ImageMaskModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( ImageMaskExceptions, E_IMAGEMASK, E_IMAGEMASK_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module ImageMaskModule = {
  ImageMaskName,
  ImageMaskVers,
  ImageMaskCopy,
  COMPILE_DATE,
  ImageMaskModuleInit,
  NULL,
  NULL,
};
