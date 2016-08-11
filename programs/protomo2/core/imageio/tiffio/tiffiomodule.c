/*----------------------------------------------------------------------------*
*
*  tiffiomodule.c  -  imageio: TIFF files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tiffiocommon.h"
#include "imageiocommon.h"
#include "imageioformat.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TiffioExceptions[ E_TIFFIO_MAXCODE - E_TIFFIO ] = {
  { "E_TIFFIO",      "internal error ("TiffioName")" },
  { "E_TIFFIO_ERR",  "tiff i/o error: " },
  { "E_TIFFIO_IMPL", "unsupported tiff feature" },
};


/* variables */

TiffioOptions TiffioOpt = {
  TIFFIO_ORI_TOP,
  300,
  COMPRESSION_LZW
};


/* formats */

static const ImageioFormat TIFFFormat = {
  { "TIFF", 6, 0 },
  TiffioFmt,
  TiffioNew,
  TiffioOld,
  NULL,
  TiffioSyn,
  TiffioFin,
  NULL,
  NULL,
  NULL,
  TiffioGet,
  &TiffioOpt,
  ImageioCapLib | ImageioCapLoad,
  50
};


/* module initialization/finalization */

static Status TiffioModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TiffioExceptions, E_TIFFIO, E_TIFFIO_MAXCODE );
  if ( exception( status ) ) return status;

  status = ImageioFormatRegister( &TIFFFormat );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module TiffioModule = {
  TiffioName,
  TiffioVers,
  TiffioCopy,
  COMPILE_DATE,
  TiffioModuleInit,
  NULL,
  NULL,
};
