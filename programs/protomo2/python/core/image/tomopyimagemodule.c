/*----------------------------------------------------------------------------*
*
*  tomopyimagemodule.c  -  tomopy: image handling
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomopyimagecommon.h"
#include "tomopygtk.h"
#include "tomopyeman.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomoPyImageExceptions[ E_TOMOPYIMAGE_MAXCODE - E_TOMOPYIMAGE ] = {
  { "E_TOMOPYIMAGE",      "internal error ("TomoPyImageName")"  },
  { "E_TOMOPYIMAGE_GTK",  "display function is disabled"        },
  { "E_TOMOPYIMAGE_EMAN", "EMAN libraries have not been loaded" },
};


/* variables */

void *TomoPyImageGtkFn = NULL;
void *TomoPyImageEmanFn = NULL;


/* module initialization/finalization */

static Status TomoPyImageModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomoPyImageExceptions, E_TOMOPYIMAGE, E_TOMOPYIMAGE_MAXCODE );
  if ( exception( status ) ) return status;

  status = ModuleDynRegister( TomoPyName "gtk.so", "TomoPyGtkModule", TomoPyGtkName, TomoPyGtkVers, &TomoPyImageGtkFn );
  if ( exception( status ) ) ExceptionClear();

  status = ModuleDynRegister( TomoPyName "eman.so", "TomoPyEmanModule", TomoPyEmanName, TomoPyEmanVers, &TomoPyImageEmanFn );
  if ( exception( status ) ) ExceptionClear();

  return E_NONE;

}


/* module descriptor */

const Module TomoPyImageModule = {
  TomoPyImageName,
  TomoPyImageVers,
  TomoPyImageCopy,
  COMPILE_DATE,
  TomoPyImageModuleInit,
  NULL,
  NULL,
};
