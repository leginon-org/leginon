/*----------------------------------------------------------------------------*
*
*  tomomapout.c  -  core: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomomap.h"
#include "imageio.h"
#include "strings.h"
#include "exception.h"
#include <stdio.h>
#include <stdlib.h>


/* functions */

extern Status TomomapOut
              (const char *prfx,
               const char *sffx,
               const Size number,
               const Size dim,
               const Size *len,
               const Index *low,
               const Type type,
               const ImageAttr attr,
               const void *addr)

{
  char numbuf[64];
  Status status;

  if ( ( prfx == NULL ) || !*prfx ) prfx = "noname";

  sprintf( numbuf, "_%"SizeU".img", number );

  char *path = StringConcat( prfx, sffx, numbuf, NULL );
  if ( path == NULL ) return pushexception( E_MALLOC );

  const Image img = { dim, (Size *)len, (Index *)low, type, attr };

  status = ImageioOut( path, &img, addr, NULL );
  logexception( status );

  free( path );

  return status;

}
