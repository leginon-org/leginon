/*----------------------------------------------------------------------------*
*
*  guigtkmodule.c  -  guigtk: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "guigtk.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage GuigtkExceptions[ E_GUIGTK_MAXCODE - E_GUIGTK ] = {
  { "E_GUIGTK",        "internal error ("GuigtkName")"  },
  { "E_GUIGTK_INIT",   "GTK initialization error"       },
  { "E_GUIGTK_GLINIT", "GTK GLext initialization error" },
  { "E_GUIGTK_VISUAL", "no OpenGL-capable visual found" },
  { "E_GUIGTK_GLCAP",  "cannot set OpenGL capability"   },
  { "E_GUIGTK_GLDRAW", "GL drawable begin failed"       },
};


/* module initialization/finalization */

static Status GuigtkModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( GuigtkExceptions, E_GUIGTK, E_GUIGTK_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module GuigtkModule = {
  GuigtkName,
  GuigtkVers,
  GuigtkCopy,
  COMPILE_DATE,
  GuigtkModuleInit,
  NULL,
  NULL,
};
