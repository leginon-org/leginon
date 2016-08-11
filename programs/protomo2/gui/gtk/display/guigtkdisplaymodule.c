/*----------------------------------------------------------------------------*
*
*  guigtkdisplaymodule.c  -  guigtk: EM image viewer
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "guigtkdisplay.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage GuigtkDisplayExceptions[ E_GUIGTKDISPLAY_MAXCODE - E_GUIGTKDISPLAY ] = {
  { "E_GUIGTKDISPLAY", "internal error ("GuigtkDisplayName")" },
};


/* module initialization/finalization */

static Status GuigtkDisplayModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( GuigtkDisplayExceptions, E_GUIGTKDISPLAY, E_GUIGTKDISPLAY_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module GuigtkDisplayModule = {
  GuigtkDisplayName,
  GuigtkDisplayVers,
  GuigtkDisplayCopy,
  COMPILE_DATE,
  GuigtkDisplayModuleInit,
  NULL,
  NULL,
};
