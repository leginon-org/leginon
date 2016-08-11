/*----------------------------------------------------------------------------*
*
*  emiomodule.c  -  imageio: em files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "emio.h"
#include "imageiocommon.h"
#include "imageiodefault.h"
#include "imageioformat.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage EMioExceptions[ E_EMIO_MAXCODE - E_EMIO ] = {
  { "E_EMIO",     "internal error ("EMioName")" },
  { "E_EMIO_HDR", "invalid EM file header" },
};


/* formats */

static const ImageioFormat EMFormat = {
  { "EM", 0, 0 },
  EMFmt,
  EMNew,
  EMOld,
  ImageioFls,
  EMHeaderWrite,
  ImageioFin,
  EMSiz,
  ImageioMmapAdr,
  NULL,
  EMGet,
  NULL,
  ImageioCapUnix | ImageioCapStd | ImageioCapMmap | ImageioCapLoad,
  40
};


/* module initialization/finalization */

static Status EMioModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( EMioExceptions, E_EMIO, E_EMIO_MAXCODE );
  if ( exception( status ) ) return status;

  status = ImageioFormatRegister( &EMFormat );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module EMioModule = {
  EMioName,
  EMioVers,
  EMioCopy,
  COMPILE_DATE,
  EMioModuleInit,
  NULL,
  NULL,
};
