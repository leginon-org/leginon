/*----------------------------------------------------------------------------*
*
*  tomoseriesoutname.c  -  series: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoseries.h"
#include "strings.h"
#include "exception.h"
#include <stdio.h>
#include <stdlib.h>


/* functions */

extern char *TomoseriesOutName
             (const Tomoseries *series,
              const char *sffx)

{
  char numbuf[64];
  char *path;

  if ( argcheck( series == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  int cycle = TomometaGetCycle( series->meta );

  if ( cycle < 0 ) {
    *numbuf = 0;
  } else {
    sprintf( numbuf, "%02d", cycle );
  }

  path = StringConcat( series->outprfx, numbuf, sffx, NULL );
  if ( path == NULL ) {
    pushexception( E_MALLOC );
  } else if ( TomodataDir( path ) ) {
    free( path ); path = NULL;
  }

  return path;

}
