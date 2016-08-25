/*----------------------------------------------------------------------------*
*
*  tomodiagn.c  -  align: diagnostic output
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomodiagncommon.h"
#include "strings.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

extern Tomodiagn *TomodiagnCreate
                  (const Tomoseries *series,
                   const char *sffx,
                   const Image *image)

{
  Size len[3];
  Index low[3];
  Status status;

  Tomodiagn *diagn = malloc( sizeof(Tomodiagn) );
  if ( diagn == NULL ) { pushexception( E_MALLOC ); return NULL; }

  char *path = TomoseriesOutName( series, sffx );
  if ( testcondition( path == NULL ) ) goto error1;

  ImageioParam param = ImageioParamDefault;
  param.mode = ImageioModeDel;
  param.cap = ImageioCapUnix;

  Image img = *image;
  img.dim = 3;
  img.len = len;
  img.low = low;
  len[0] = image->len[0];
  len[1] = image->len[1];
  len[2] = series->tilt->images;
  low[0] = ( image->low == NULL ) ? 0 : image->low[0];
  low[1] = ( image->low == NULL ) ? 0 : image->low[1];
  low[2] = 0;

  Imageio *imageio = ImageioCreate( path, &img, &param );
  if ( testcondition( imageio == NULL ) ) goto error2;

  status = ImageioResize( imageio, len[2] );
  if ( exception( status ) ) goto error3;

  free( path );

  diagn->handle = imageio;
  diagn->size = len[0] * len[1];
  diagn->status = E_NONE;

  return diagn;

  /* error handling */

  error3: ImageioClose( imageio );
  error2: free( path );
  error1: free( diagn );

  return NULL;

}


extern Status TomodiagnDestroy
              (Tomodiagn *diagn)

{
  Status stat, status = E_NONE;

  if ( argcheck( diagn == NULL ) ) return pushexception( E_ARGVAL );

  if ( diagn->handle != NULL ) {

    stat = ImageioClose( diagn->handle );
    if ( exception( stat ) ) status = stat;

  }

  free( diagn );

  return status;

}
