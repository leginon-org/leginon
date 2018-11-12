/*----------------------------------------------------------------------------*
*
*  tomoseriesextract.c  -  series: tomography
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
#include "exception.h"
#include "message.h"
#include <stdio.h>
#include <stdlib.h>


/* functions */

#define logbuflen 96

extern Status TomoseriesExtract
              (const Tomoseries *series,
               const Window *win,
               const Size index,
               Coord B[3][3],
               Coord b[2],
               Size dstlen[2],
               Size dstori[2],
               Index dstlow[2],
               Real **dstaddr)

{
  Size len[2], ori[2];
  Size count, dstsize;
  char logbuf[logbuflen];
  Status status;

  if ( argcheck( series == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( dstlen == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( dstaddr == NULL ) ) return pushexception( E_ARGVAL );

  Tomodata *data = series->data;
  TomodataDscr *dscr = data->dscr + index;
  Tomogeom *geom = series->geom + index;

  TomoseriesResampleGeom3( dscr, series->sampling, geom->A, geom->Ap[2], B, b );

  Real *extraddr = malloc( dscr->size * sizeof(Real) );
  if ( extraddr == NULL ) return pushexception( E_MALLOC );

  void *addr = TomodataBeginRead( data->cache, dscr, index );
  status = testcondition( addr == NULL );
  if ( status ) goto error1;

  if ( win->len == NULL ) {
    ori[0] = 0;
    ori[1] = 0;
    len[0] = dscr->img.len[0];
    len[1] = dscr->img.len[1];
    dstsize = dscr->size;
  } else {
    status = TomogeomAreaMax( win->len[0], win->len[1], win->len[2], B, b, len, ori, &dstsize );
    if ( pushexception( status ) ) goto error2;
  }

  Window extr = WindowInitializer;
  extr.dim = 2;
  extr.len = len;
  extr.size = len[0] * len[1];
  extr.area = win->area;
  status = WindowCut( dscr->img.len, dscr->img.type, addr, ori, &extr, extraddr, &count, NULL );
  if ( status ) {
    if ( status != E_WINDOW_AREA ) return pushexception( status );
    if ( series->flags & TomoLog ) {
      Coord a = 100.0 * count / dstsize;
      TomodataLogString( data, data->dscr, index, logbuf, logbuflen );
      MessageFormat( "%s extracted area is too small [%.1"CoordF"%%]\n", logbuf, a );
    }
  } else if ( series->flags & TomoLog ) {
    TomodataLogString( data, data->dscr, index, logbuf, logbuflen );
    MessageFormat( "%s extracted\n", logbuf );
  }

  if ( extr.size < dscr->size ) {
    Real *ptr = realloc( extraddr, extr.size * sizeof(Real) );
    if ( ptr == NULL ) { status = pushexception( E_MALLOC ); goto error2; }
    extraddr = ptr;
  }

  status = TomodataEndRead( data->cache, dscr, index, addr );
  if ( exception( status ) ) return status;

  if ( dstlen != NULL ) {
    dstlen[0] = len[0];
    dstlen[1] = len[1];
  }

  if ( dstori != NULL ) {
    dstori[0] = ori[0];
    dstori[1] = ori[1];
  }

  if ( dstlow != NULL ) {
    dstlow[0] = dscr->img.low[0] + ori[0];
    dstlow[1] = dscr->img.low[1] + ori[1];
  }

  *dstaddr = extraddr;

  return E_NONE;

  error2: TomodataEndRead( data->cache, dscr, index, addr );
  error1: free( extraddr );

  return status;

}


extern Status TomoseriesExtractWrite
              (const Tomoseries *series,
               const Window *win,
               const Size nz,
               const char *path)

{
  Coord B[3][3], b[2];
  Size len[2];
  Index low[2];
  Real *buf;
  char *ext, numbuf[64];
  char *wpath = NULL;
  Status status;

  if ( argcheck( series == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( win == NULL ) ) return pushexception( E_ARGVAL );

  if ( ( path == NULL ) || !*path ) {
    wpath = TomoseriesOutName( series, NULL );
    status = testcondition( wpath == NULL );
    if ( status ) return status;
    path = wpath;
  }

  Size winlen[3] = { win->len[0], win->len[1], nz };
  Image img = { 2, len, low, TypeReal, ImageRealspc };

  Window extr = WindowInitializer;
  extr.len = winlen;
  extr.area = win->area;

  for ( Size index = 0; index < series->tilt->images; index++ ) {

    status = TomoseriesExtract( series, &extr, index, B, b, len, NULL, low, &buf );
    if ( exception( status ) ) goto error1;

    Size number = series->tilt->tiltimage[index].number;
    sprintf( numbuf, "_ext_%"SizeU".img", number );
    ext = StringConcat( path, numbuf, NULL );
    if ( ext == NULL ) { status = exception( E_MALLOC ); goto error2; }

    status = ImageioOut( ext, &img, buf, NULL );
    if ( exception( status ) ) goto error3;

    free( ext );
    free( buf );

  }

  if ( wpath != NULL ) free( wpath );

  return E_NONE;

  error3: free( ext );
  error2: free( buf );
  error1: if ( wpath != NULL ) free( wpath );

  return status;

}
