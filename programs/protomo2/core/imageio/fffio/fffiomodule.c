/*----------------------------------------------------------------------------*
*
*  fffiomodule.c  -  imageio: FFF files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "fffio.h"
#include "imageiocommon.h"
#include "imageiodefault.h"
#include "imageioformat.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage FFFioExceptions[ E_FFFIO_MAXCODE - E_FFFIO ] = {
  { "E_FFFIO", "internal error ("FFFioName")" },
};


/* formats */

static const ImageioFormat FFFFormat = {
  { "FFF", 1, 8 },
  FFFFmt,
  FFFNew,
  FFFOld,
  ImageioFls,
  FFFMetaWrite,
  FFFFin,
  FFFSiz,
  ImageioMmapAdr,
  FFFExtra,
  FFFGet,
  NULL,
  ImageioCapUnix | ImageioCapStd | ImageioCapMmap | ImageioCapLoad,
  101
};

#ifdef FFFSupportVersion100

static const ImageioFormat FFFV100Format = {
  { "FFF", 1, 0 },
  FFFFmt,
  NULL,
  FFFOld,
  NULL,
  NULL,
  FFFFin,
  FFFSiz,
  ImageioMmapAdr,
  NULL,
  FFFGet,
  NULL,
  ImageioCapUnix | ImageioCapStd | ImageioCapMmap | ImageioCapLoad,
  100
};

#endif 


/* module initialization/finalization */

static Status FFFioModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( FFFioExceptions, E_FFFIO, E_FFFIO_MAXCODE );
  if ( exception( status ) ) return status;

  status = ImageioFormatRegister( &FFFFormat );
  if ( exception( status ) ) return status;

#ifdef FFFSupportVersion100
  status = ImageioFormatRegister( &FFFV100Format );
  if ( exception( status ) ) return status;
#endif 

  return E_NONE;

}


/* module descriptor */

const Module FFFioModule = {
  FFFioName,
  FFFioVers,
  FFFioCopy,
  COMPILE_DATE,
  FFFioModuleInit,
  NULL,
  NULL,
};
