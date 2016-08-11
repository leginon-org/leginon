/*----------------------------------------------------------------------------*
*
*  spideriomodule.c  -  imageio: spider files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "spiderio.h"
#include "imageiocommon.h"
#include "imageiodefault.h"
#include "imageioformat.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage SpiderioExceptions[ E_SPIDERIO_MAXCODE - E_SPIDERIO ] = {
  { "E_SPIDERIO",       "internal error ("SpiderioName")" },
  { "E_SPIDERIO_HDR",   "invalid Spider header" },
  { "E_SPIDERIO_STACK", "image stacks not supported" },
};


/* formats */

static const ImageioFormat SpiderFormat = {
  { "SPIDER", 0, 0 },
  SpiderFmt,
  SpiderNew,
  SpiderOld,
  ImageioFls,
  SpiderHeaderWrite,
  ImageioFin,
  SpiderSiz,
  ImageioMmapAdr,
  NULL,
  SpiderGet,
  NULL,
  ImageioCapUnix | ImageioCapStd | ImageioCapMmap | ImageioCapLoad,
  80
};


/* module initialization/finalization */

static Status SpiderioModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( SpiderioExceptions, E_SPIDERIO, E_SPIDERIO_MAXCODE );
  if ( exception( status ) ) return status;

  status = ImageioFormatRegister( &SpiderFormat );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module SpiderioModule = {
  SpiderioName,
  SpiderioVers,
  SpiderioCopy,
  COMPILE_DATE,
  SpiderioModuleInit,
  NULL,
  NULL,
};
