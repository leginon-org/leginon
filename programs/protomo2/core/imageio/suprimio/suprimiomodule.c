/*----------------------------------------------------------------------------*
*
*  suprimiomodule.c  -  imageio: suprim files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "suprimio.h"
#include "imageiocommon.h"
#include "imageiodefault.h"
#include "imageioformat.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage SuprimioExceptions[ E_SUPRIMIO_MAXCODE - E_SUPRIMIO ] = {
  { "E_SUPRIMIO",     "internal error ("SuprimioName")" },
  { "E_SUPRIMIO_HDR", "invalid Suprim header" },
  { "E_SUPRIMIO_TRC", "invalid Suprim trace"  },
};


/* formats */

static const ImageioFormat SuprimFormat = {
  { "SUPRIM", 0, 0 },
  SuprimFmt,
  SuprimNew,
  SuprimOld,
  ImageioFls,
  SuprimHeaderWrite,
  ImageioFin,
  SuprimSiz,
  ImageioMmapAdr,
  NULL,
  SuprimGet,
  NULL,
  ImageioCapUnix | ImageioCapStd | ImageioCapMmap | ImageioCapLoad,
  60
};


/* module initialization/finalization */

static Status SuprimioModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( SuprimioExceptions, E_SUPRIMIO, E_SUPRIMIO_MAXCODE );
  if ( exception( status ) ) return status;

  status = ImageioFormatRegister( &SuprimFormat );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module SuprimioModule = {
  SuprimioName,
  SuprimioVers,
  SuprimioCopy,
  COMPILE_DATE,
  SuprimioModuleInit,
  NULL,
  NULL,
};
