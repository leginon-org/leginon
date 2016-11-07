/*----------------------------------------------------------------------------*
*
*  tomoserieswindow.c  -  series: tomography
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

static Status TomoseriesWindowResample
              (const Tomoseries *series,
               const Window *win,
               const Size index,
               Tomogeom *geom,
               Real *addr,
               Bool aligned)

{
  Coord (*Ap)[2] = geom->Ap;
  Status status;

  if ( aligned ) {

    if ( ( ( geom->Aa[0][0] == 0 ) && ( geom->Aa[0][1] == 0 ) )
      || ( ( geom->Aa[1][0] == 0 ) && ( geom->Aa[1][1] == 0 ) ) ) {
      memset( addr, 0, win->size * sizeof(*addr) );
      return E_NONE;
    }

    Ap = geom->Aa;

  }

  status = TomoseriesResample( series, win, index, Ap, addr, NULL, NULL );
  if ( exception( status ) ) {
    if ( status == E_WINDOW_AREA ) {
      ExceptionClear();
      status = E_NONE;
    }
  }

  return status;

}


extern Status TomoseriesWindow
              (const Tomoseries *series,
               const Window *win,
               Image *img,
               Real **addr,
               Bool aligned)

{
  Image dst;
  Real *winbuf;
  Size size, winsize;
  Status status;

  if ( argcheck( series == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( win  == NULL ) ) return pushexception( E_ARGVAL );

  status = MulSize( win->size, series->tilt->images, &winsize );
  if ( pushexception( status ) ) return status;

  if ( img != NULL ) {
    status = ImageMetaAlloc( 3, &dst );
    if ( pushexception( status ) ) return status;
  }

  if ( addr != NULL ) {

    status = MulSize( winsize, sizeof(*winbuf), &size );
    if ( pushexception( status ) ) return status;

    winbuf = malloc( size );
    if ( winbuf == NULL ) { status = pushexception( E_MALLOC ); goto error1; }

    Tomogeom *geom = series->geom;
    Real *buf = winbuf;

    for ( Size index = 0; index < series->tilt->images; index++, geom++, buf += win->size ) {

      status = TomoseriesWindowResample( series, win, index, geom, buf, aligned );
      if ( exception( status ) ) goto error2;

    }

  }

  if ( img != NULL ) {

    img->dim = 3;
    img->len = dst.len;
    img->low = dst.low;
    img->type = TypeReal;
    img->attr = ImageRealspc;
    img->len[0] = win->len[0];
    img->len[1] = win->len[1];
    img->len[2] = series->tilt->images;
    img->low[0] = -(Index)( img->len[0] / 2 );
    img->low[1] = -(Index)( img->len[1] / 2 );
    img->low[2] = 0;

  }

  if ( addr != NULL ) *addr = winbuf;

  return E_NONE;

  error2: free( winbuf );
  error1: if ( img != NULL ) { free( dst.len ); free( dst.low ); }

  return status;

}


extern Status TomoseriesWindowImage
              (const Tomoseries *series,
               const Window *win,
               const Size index,
               Image *img,
               void **addr,
               Bool aligned)

{
  Image dst;
  Status status;

  if ( argcheck( series == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( win == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( img  == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return pushexception( E_ARGVAL );

  if ( index >= series->tilt->images ) return pushexception( E_ARGVAL );

  Real *dstaddr = malloc( win->size * sizeof(*dstaddr) );
  if ( dstaddr == NULL ) return pushexception( E_MALLOC );

  status = TomoseriesWindowResample( series, win, index, series->geom + index, dstaddr, aligned );
  if ( exception( status ) ) goto error;

  status = ImageMetaAlloc( 2, &dst );
  if ( pushexception( status ) ) goto error;

  img->dim = 2;
  img->len = dst.len;
  img->low = dst.low;
  img->type = TypeReal;
  img->attr = ImageRealspc;
  img->len[0] = win->len[0];
  img->len[1] = win->len[1];
  img->low[0] = -(Index)( img->len[0] / 2 );
  img->low[1] = -(Index)( img->len[1] / 2 );

  *addr = dstaddr;

  return E_NONE;

  error: free( dstaddr );

  return status;

}


extern Status TomoseriesWindowWrite
              (const Tomoseries *series,
               const Window *win,
               const char *path,
               Bool aligned)

{
  char *wpath = NULL;
  Status status, stat;

  if ( argcheck( series == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( win == NULL ) ) return pushexception( E_ARGVAL );

  if ( ( path == NULL ) || !*path ) {
    wpath = TomoseriesOutName( series, "_win.img" );
    status = testcondition( wpath == NULL );
    if ( status ) return status;
    path = wpath;
  }

  Image img;
  status = TomoseriesWindow( series, win, &img, NULL, False );
  if ( exception( status ) ) goto exit1;

  Real *buf = WindowAlloc( win );
  if ( buf == NULL ) { status = pushexception( E_MALLOC ); goto exit2; }

  ImageioParam param = ImageioParamDefault;
  param.mode = ImageioModeDel;
  param.cap = ImageioCapUnix;

  Imageio *imageio = ImageioCreate( path, &img, &param );
  status = testcondition( imageio == NULL );
  if ( status ) goto exit3;


  Tomogeom *geom = series->geom;
  Offset doffs = 0;

  for ( Size index = 0; index < series->tilt->images; index++, geom++, doffs += win->size ) {

    status = TomoseriesWindowResample( series, win, index, geom, buf, aligned );
    if ( exception( status ) ) goto exit4;

    status = ImageioWrite( imageio, doffs, win->size, buf );
    if ( exception( status ) ) goto exit4;

  }

  status = ImageioUndel( imageio );
  logexception( status );

  exit4:

  stat = ImageioClose( imageio );
  if ( exception( stat ) ) if ( !status ) status = stat;

  exit3: free( buf );

  exit2: free( img.len ); free( img.low );

  exit1: if ( wpath != NULL ) free( wpath );

  return status;

}
