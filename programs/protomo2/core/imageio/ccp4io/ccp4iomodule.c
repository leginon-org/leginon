/*----------------------------------------------------------------------------*
*
*  ccp4iomodule.c  -  imageio: CCP4 files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "ccp4io.h"
#include "imageiocommon.h"
#include "imageiodefault.h"
#include "imageioformat.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage CCP4ioExceptions[ E_CCP4IO_MAXCODE - E_CCP4IO ] = {
  { "E_CCP4IO",      "internal error ("CCP4ioName")" },
  { "E_CCP4IO_FOU",  "unsupported Fourier transform size" },
  { "E_CCP4IO_AXIS", "unsupported axis order" },
};


/* formats */

static const ImageioFormat CCP4Format = {
  { "CCP4", 0, 0 },
  CCP4Fmt,
  CCP4New,
  CCP4Old,
  ImageioFls,
  CCP4HeaderWrite,
  ImageioFin,
  CCP4Siz,
  ImageioMmapAdr,
  CCP4Extra,
  CCP4Get,
  NULL,
  ImageioCapUnix | ImageioCapStd | ImageioCapMmap | ImageioCapLoad,
  91
};

static const ImageioFormat MRCFormat = {
  { "MRC", 0, 0 },
  CCP4Fmt,
  CCP4New,
  CCP4Old,
  ImageioFls,
  CCP4HeaderWrite,
  ImageioFin,
  CCP4Siz,
  ImageioMmapAdr,
  CCP4Extra,
  CCP4Get,
  NULL,
  ImageioCapUnix | ImageioCapStd | ImageioCapMmap | ImageioCapLoad,
  90
};


/* module initialization/finalization */

static Status CCP4ioModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( CCP4ioExceptions, E_CCP4IO, E_CCP4IO_MAXCODE );
  if ( exception( status ) ) return status;

  status = ImageioFormatRegister( &CCP4Format );
  if ( exception( status ) ) return status;

  status = ImageioFormatRegister( &MRCFormat );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module CCP4ioModule = {
  CCP4ioName,
  CCP4ioVers,
  CCP4ioCopy,
  COMPILE_DATE,
  CCP4ioModuleInit,
  NULL,
  NULL,
};
