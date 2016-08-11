/*----------------------------------------------------------------------------*
*
*  tomopygtkmodule.c  -  gtk wrapper library
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomopy.h"
#include "tomopygtk.h"
#include "guigtkdisplay.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* modules */

extern const Module GraphModule;
extern const Module GuigtkModule;
extern const Module GuigtkDisplayModule;


/* functions */

static Status TomoPyGtkDisplay
              (const Image *image,
               const void *addr)

{
  Status status;

  GuigtkDisplayParam param = GuigtkDisplayParamInitializer;
  param.flags = GuigtkDisplayDetach;

  status = GuigtkDisplayCreate( image, addr, &param );
  logexception( status );

  return status;

}


/* variables */

static TomoPyGtkFn TomoPyGtkFunctions = {
  TomoPyGtkDisplay,
};


/* module initialization/finalization */

static Status TomoPyGtkModuleInit
              (void **data)

{
  Status status;

  status = GraphModule.init( NULL );
  if ( exception( status ) ) return status;

  status = GuigtkModule.init( NULL );
  if ( exception( status ) ) return status;

  status = GuigtkDisplayModule.init( NULL );
  if ( exception( status ) ) return status;

  if ( data == NULL ) return pushexception( E_INTERNAL );
  *data = &TomoPyGtkFunctions;

  return E_NONE;

}


/* module descriptor */

const Module TomoPyGtkModule = {
  TomoPyGtkName,
  TomoPyGtkVers,
  TomoPyGtkCopy,
  COMPILE_DATE,
  TomoPyGtkModuleInit,
  NULL,
  NULL,
};
