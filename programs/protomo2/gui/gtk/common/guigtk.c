/*----------------------------------------------------------------------------*
*
*  guigtk.c  -  guigtk: common routines
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
#include "graph.h"
#include "exception.h"
#include "module.h"


/* variables */

Bool GuigtkLog = False;


/* functions */

extern Status GuigtkInit()

{
  static Bool initgtk = False;
  static Bool initgtkgl = False;

  if ( !initgtk ) {
    if ( !gtk_init_check( CoreArgc, &CoreArgv ) ) {
      return pushexception( E_GUIGTK_INIT );
    }
    initgtk = True;
  }

  if ( !initgtkgl ) {
    if ( !gtk_gl_init_check( CoreArgc, &CoreArgv ) ) {
      return pushexception( E_GUIGTK_INIT );
    }
    initgtkgl = True;
  }

  return E_NONE;

}
