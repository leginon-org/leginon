/*----------------------------------------------------------------------------*
*
*  tomoseriesarea.c  -  series: tomography
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
#include "imageio.h"
#include "strings.h"
#include "baselib.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern Status TomoseriesArea
              (const Tomoseries *series,
               const Window *win,
               Image *img,
               uint16_t **addr,
               Bool aligned)

{
  Image dst;
  Status status;

  if ( argcheck( series == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( win  == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return pushexception( E_ARGVAL );

  uint16_t *winbuf = malloc( win->size * sizeof(*winbuf) );
  if ( winbuf == NULL ) return pushexception( E_MALLOC );

  uint16_t *buf = malloc( win->size * sizeof(*buf) );
  if ( buf == NULL ) { status = pushexception( E_MALLOC ); goto error1; }
  memset( buf, 0, win->size * sizeof(*buf) );

  if ( img != NULL ) {
    status = ImageMetaAlloc( 2, &dst );
    if ( pushexception( status ) ) goto error2;
  }

  TomotiltImage *tilt = series->tilt->tiltimage;
  Tomogeom *geom = series->geom;

  for ( Size index = 0; index < series->tilt->images; index++, tilt++, geom++ ) {

    if ( SelectExclude( series->selection, series->exclusion, tilt->number ) ) {

      Coord (*Ap)[2] = geom->Ap;

      if ( aligned ) {
        if ( ( geom->Aa[0][0] != 0 ) || ( geom->Aa[0][1] != 0 )
          || ( geom->Aa[1][0] != 0 ) || ( geom->Aa[1][1] != 0 ) ) {
          Ap = geom->Aa;
        }
      }

      status = TomoseriesResampleArea( series, win, index, Ap, winbuf );
      if ( exception( status ) ) goto error3;

      for ( Size i = 0; i < win->size; i++ ) {
        if ( winbuf[i] && ( buf[i] < UINT16_MAX ) ) buf[i]++;
      }

    }

  }

  if ( img != NULL ) {
    img->dim = 2;
    img->len = dst.len;
    img->low = dst.low;
    img->type = TypeUint16;
    img->attr = ImageRealspc;
    img->len[0] = win->len[0];
    img->len[1] = win->len[1];
    img->low[0] = -(Index)( img->len[0] / 2 );
    img->low[1] = -(Index)( img->len[1] / 2 );
  }

  *addr = buf;

  free( winbuf );

  return E_NONE;

  error3: if ( img != NULL ) { free( dst.len ); free( dst.low ); }
  error2: free( buf );
  error1: free( winbuf );
  return status;

}


extern Status TomoseriesAreaWrite
              (const Tomoseries *series,
               const Window *win,
               const char *path,
               Bool aligned)

{
  char *wpath = NULL;
  Status status;

  if ( argcheck( series == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( win == NULL ) ) return pushexception( E_ARGVAL );

  if ( ( path == NULL ) || !*path ) {
    wpath = TomoseriesOutName( series, "_area.img" );
    status = testcondition( wpath == NULL );
    if ( status ) return status;
    path = wpath;
  }

  Image img; uint16_t *area;
  status = TomoseriesArea( series, win, &img, &area, aligned );
  if ( exception( status ) ) goto exit;

  status = ImageioOut( path, &img, area, NULL );
  logexception( status );

  free( img.len ); free( img.low ); free( area );

  exit: if ( wpath != NULL ) free( wpath );

  return status;

}
