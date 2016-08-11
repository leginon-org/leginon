/*----------------------------------------------------------------------------*
*
*  imagectfmodule.c  -  image: contrast transfer function
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagectf.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage ImageCTFExceptions[ E_IMAGECTF_MAXCODE - E_IMAGECTF ] = {
  { "E_IMAGECTF",      "internal error ("ImageCTFName")" },
  { "E_IMAGECTF_DIM",  "invalid image dimension for CTF" },
  { "E_IMAGECTF_TYPE", "invalid data type for CTF"       },
};


/* module initialization/finalization */

static Status ImageCTFModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( ImageCTFExceptions, E_IMAGECTF, E_IMAGECTF_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module ImageCTFModule = {
  ImageCTFName,
  ImageCTFVers,
  ImageCTFCopy,
  COMPILE_DATE,
  ImageCTFModuleInit,
  NULL,
  NULL,
};
