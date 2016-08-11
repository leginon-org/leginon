/*----------------------------------------------------------------------------*
*
*  tomogeom.c  -  tomography: tilt geometry
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomogeom.h"
#include "exception.h"


/* functions */

extern Status TomogeomInit
              (const Tomotilt *tilt,
               Coord A[3][3],
               const Coord b[3],
               Tomogeom *geom)

{
  Status status;

  if ( tilt == NULL ) return pushexception( E_ARGVAL );
  if ( geom == NULL ) return pushexception( E_ARGVAL );

  for ( Size index = 0; index < tilt->images; index++, geom++ ) {

    status = TomogeomLoad( tilt, index, A, b, geom );
    if ( exception( status ) ) return status;

  }

  return E_NONE;

}
