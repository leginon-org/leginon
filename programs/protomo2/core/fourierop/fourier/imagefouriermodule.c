/*----------------------------------------------------------------------------*
*
*  imagefouriermodule.c  -  fourierop: image transforms
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagefourier.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage ImageFourierExceptions[ E_IMAGEFOURIER_MAXCODE - E_IMAGEFOURIER ] = {
  { "E_IMAGEFOURIER", "internal error ("ImageFourierName")" },
};


/* module initialization/finalization */

static Status ImageFourierModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( ImageFourierExceptions, E_IMAGEFOURIER, E_IMAGEFOURIER_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module ImageFourierModule = {
  ImageFourierName,
  ImageFourierVers,
  ImageFourierCopy,
  COMPILE_DATE,
  ImageFourierModuleInit,
  NULL,
  NULL,
};
