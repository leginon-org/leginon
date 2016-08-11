/*----------------------------------------------------------------------------*
*
*  imagemodule.c  -  image: images
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "image.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage ImageExceptions[ E_IMAGE_MAXCODE - E_IMAGE ] = {
  { "E_IMAGE", "internal error ("ImageName")"    },
  { "E_IMAGE_DIM",    "invalid image dimension"  },
  { "E_IMAGE_SIZE",   "invalid image size"       },
  { "E_IMAGE_ZERO",   "zero size image"          },
  { "E_IMAGE_BOUNDS", "out of bounds"            },
  { "E_IMAGE_TYPE",   "invalid image data type"  },
  { "E_IMAGE_ATTR",   "invalid image attributes" },
  { "E_IMAGE_SYM",    "invalid image bounds"     },
  { "E_IMAGE_WINDOW", "invalid image window"     },
};


/* module initialization/finalization */

static Status ImageModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( ImageExceptions, E_IMAGE, E_IMAGE_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module ImageModule = {
  ImageName,
  ImageVers,
  ImageCopy,
  COMPILE_DATE,
  ImageModuleInit,
  NULL,
  NULL,
};
