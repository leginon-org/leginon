/*----------------------------------------------------------------------------*
*
*  imagearraymodule.c  -  image: array operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagearray.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage ImageArrayExceptions[ E_IMAGEARRAY_MAXCODE - E_IMAGEARRAY ] = {
  { "E_IMAGEARRAY",         "internal error ("ImageArrayName")" },
  { "E_IMAGEARRAY_SYMSIZE", "invalid image size "               },
  { "E_IMAGEARRAY_ASYM",    "image is asymmetric"               },
};


/* module initialization/finalization */

static Status ImageArrayModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( ImageArrayExceptions, E_IMAGEARRAY, E_IMAGEARRAY_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module ImageArrayModule = {
  ImageArrayName,
  ImageArrayVers,
  ImageArrayCopy,
  COMPILE_DATE,
  ImageArrayModuleInit,
  NULL,
  NULL,
};
