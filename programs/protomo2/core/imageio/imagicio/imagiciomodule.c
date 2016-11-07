/*----------------------------------------------------------------------------*
*
*  imagiciomodule.c  -  imageio: imagic files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagicio.h"
#include "imageiocommon.h"
#include "imageiodefault.h"
#include "imageioformat.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage ImagicioExceptions[ E_IMAGICIO_MAXCODE - E_IMAGICIO ] = {
  { "E_IMAGICIO",       "internal error ("ImagicioName")" },
  { "E_IMAGICIO_NAME",  "invalid IMAGIC header file name" },
  { "E_IMAGICIO_FEAT",  "unsupported IMAGIC feature" },
  { "E_IMAGICIO_FLOAT", "unsupported floating point format" },
  { "E_IMAGICIO_ALLOC", "incomplete data allocation" },
};


/* formats */

static const ImageioFormat ImagicFormat = {
  { "IMAGIC", 4, 0xd },
  ImagicFmt,
  ImagicNew,
  ImagicOld,
  ImageioFls,
  ImagicHeaderWrite,
  ImagicFin,
  ImagicSiz,
  NULL,
  ImagicExtra,
  ImagicGet,
  NULL,
  ImageioCapUnix | ImageioCapStd | ImageioCapAmap | ImageioCapLoad,
  70
};

static const ImageioFormat ImagicRawFormat = {
  { "IMAGIC-RAW", 4, 0 },
  ImagicFmt,
  ImagicNew,
  ImagicOld,
  ImageioFls,
  ImagicHeaderWrite,
  ImagicFin,
  ImagicSiz,
  ImageioMmapAdr,
  ImagicExtra,
  ImagicGet,
  NULL,
  ImageioCapUnix | ImageioCapStd | ImageioCapMmap | ImageioCapLoad,
  71
};


/* module initialization/finalization */

static Status ImagicioModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( ImagicioExceptions, E_IMAGICIO, E_IMAGICIO_MAXCODE );
  if ( exception( status ) ) return status;

  status = ImageioFormatRegister( &ImagicFormat );
  if ( exception( status ) ) return status;

  status = ImageioFormatRegister( &ImagicRawFormat );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module ImagicioModule = {
  ImagicioName,
  ImagicioVers,
  ImagicioCopy,
  COMPILE_DATE,
  ImagicioModuleInit,
  NULL,
  NULL,
};
