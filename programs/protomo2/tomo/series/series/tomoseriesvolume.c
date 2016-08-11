/*----------------------------------------------------------------------------*
*
*  tomoseriesvolume.c  -  series: tomography
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
#include "baselib.h"
#include "imageio.h"
#include "transf3.h"
#include "exception.h"
#include "message.h"
#include <stdlib.h>
#include <string.h>


/* functions */

static void TomoseriesPoint
            (Coord B[4][3],
             Coord x,
             Coord y,
             Coord r[3])

{

  Coord c0  =  B[0][0] * x  +  B[1][0] * y  +  B[3][0];
  Coord c1  =  B[0][1] * x  +  B[1][1] * y  +  B[3][1];
  Coord c2  =  B[0][2] * x  +  B[1][2] * y  +  B[3][2];

  Coord z = ( r[2] - c2 ) / B[2][2];

  r[0] = c0 + B[2][0] * z;
  r[1] = c1 + B[2][1] * z;

}


static void TomoseriesMax
            (Coord B[4][3],
             Size nz,
             Coord x,
             Coord y,
             Coord min[2],
             Coord max[2])

{
  Coord r[3];

  r[2] = -(Coord)( nz / 2 );

  TomoseriesPoint( B, x, y, r );

  if ( r[0] < min[0] ) min[0] = r[0];
  if ( r[1] < min[1] ) min[1] = r[1];

  if ( r[0] > max[0] ) max[0] = r[0];
  if ( r[1] > max[1] ) max[1] = r[1];

  if ( nz ) {

    r[2] += nz - 1;

    TomoseriesPoint( B, x, y, r );

    if ( r[0] < min[0] ) min[0] = r[0];
    if ( r[1] < min[1] ) min[1] = r[1];

    if ( r[0] > max[0] ) max[0] = r[0];
    if ( r[1] > max[1] ) max[1] = r[1];

  }

}


static Coord TomoseriesLine
             (Coord p1[2],
              Coord p2[2],
              Coord x,
              Coord y)

{

  return ( y - p1[1] ) - ( x - p1[0] ) * ( p2[1] - p1[1] ) / ( p2[0] - p1[0] );

}


static Status TomoseriesPar
              (Coord B[4][3],
               Size v[2],
               Coord z,
               Coord p[4][4])

{

  p[0][2] = z; TomoseriesPoint( B, 0,    0,    p[0] );
  p[1][2] = z; TomoseriesPoint( B, v[0], 0,    p[1] );
  p[2][2] = z; TomoseriesPoint( B, v[0], v[1], p[2] );
  p[3][2] = z; TomoseriesPoint( B, 0,    v[1], p[3] );

  p[0][3] = TomoseriesLine( p[0], p[1], p[2][0], p[2][1] );
  p[1][3] = TomoseriesLine( p[1], p[2], p[3][0], p[3][1] );
  p[2][3] = TomoseriesLine( p[2], p[3], p[0][0], p[0][1] );
  p[3][3] = TomoseriesLine( p[3], p[0], p[1][0], p[1][1] );

  if ( p[0][3] == 0 ) return exception( E_TOMOSERIES );
  if ( p[1][3] == 0 ) return exception( E_TOMOSERIES );
  if ( p[2][3] == 0 ) return exception( E_TOMOSERIES );
  if ( p[3][3] == 0 ) return exception( E_TOMOSERIES );

  return E_NONE;

}


static Bool TomoseriesInPar
            (Coord p[4][4],
             Coord x,
             Coord y)

{

  if ( p[0][3] < 0 ) {
    if ( TomoseriesLine( p[0], p[1], x, y ) >= 0 ) return False;
  } else {
    if ( TomoseriesLine( p[0], p[1], x, y ) <= 0 ) return False;
  }

  if ( p[1][3] < 0 ) {
    if ( TomoseriesLine( p[1], p[2], x, y ) >= 0 ) return False;
  } else {
    if ( TomoseriesLine( p[1], p[2], x, y ) <= 0 ) return False;
  }

  if ( p[2][3] < 0 ) {
    if ( TomoseriesLine( p[2], p[3], x, y ) >= 0 ) return False;
  } else {
    if ( TomoseriesLine( p[2], p[3], x, y ) <= 0 ) return False;
  }

  if ( p[3][3] < 0 ) {
    if ( TomoseriesLine( p[3], p[0], x, y ) >= 0 ) return False;
  } else {
    if ( TomoseriesLine( p[3], p[0], x, y ) <= 0 ) return False;
  }

  return True;

}


static Status TomoseriesVolumeUse
              (const Size nt,
               const Size len[2],
               const uint16_t *buf,
               Size low[2],
               Size high[2])

{
  const uint16_t *b;
  Size c;

  Bool f1 = True, f2 = True, f3 = True, f4 = True;

  do {

    if ( f2 ) {
      if ( high[0] < ( len[0] - 1 ) ) {
        b = buf + ( high[0] + 1 ) + low[1] * len[0]; c = 0;
        for ( Size y = low[1]; y <= high[1]; y++, b += len[0] ) {
          c += *b;
        }
        if ( c < nt * ( high[1] - low[1] + 1 ) ) {
          f2 = False;
        } else {
          high[0]++;
        }
      } else {
        f2 = False;
      }
    }

    if ( f3 ) {
      if ( high[1] < ( len[1] - 1 ) ) {
        b = buf + low[0] + ( high[1] + 1 ) * len[0]; c = 0;
        for ( Size x = low[0]; x <= high[0]; x++, b++ ) {
          c += *b;
        }
        if ( c < nt * ( high[0] - low[0] + 1 ) ) {
          f3 = False;
        } else {
          high[1]++;
        }
      } else {
        f3 = False;
      }
    }

    if ( f4 ) {
      if ( low[0] > 0 ) {
        b = buf + ( low[0] - 1 ) + low[1] * len[0]; c = 0;
        for ( Size y = low[1]; y <= high[1]; y++, b += len[0] ) {
          c += *b;
        }
        if ( c < nt * ( high[1] - low[1] + 1 ) ) {
          f4 = False;
        } else {
          low[0]--;
        }
      } else {
        f4 = False;
      }
    }

    if ( f1 ) {
      if ( low[1] > 0 ) {
        b = buf + low[0] + ( low[1] - 1 ) * len[0]; c = 0;
        for ( Size x = low[0]; x <= high[0]; x++, b++ ) {
          c += *b;
        }
        if ( c < nt * ( high[0] - low[0] + 1 ) ) {
          f1 = False;
        } else {
          low[1]--;
        }
      } else {
        f1 = False;
      }
    }

  } while ( f1 || f2 || f3 || f4 );

  return E_NONE;

}


static Status TomoseriesVolumeGeom
              (Tomogeom *geom,
               TomodataDscr *dscr,
               Coord sampling,
               Coord B[4][3],
               Size v[2])

{
  Status status;

  TomoseriesResampleGeom3( dscr, sampling, geom->A, geom->Ap[2], B, B[3] );
  B[3][2] = 0;

  status = Transf3Inv( B, B, NULL );
  if ( exception( status ) ) return status;

  v[0] = dscr->len[0] - 1;
  v[1] = dscr->len[1] - 1;

  return E_NONE;

}


extern Status TomoseriesVolume
              (const Tomoseries *series,
               const Size nz,
               Image *img,
               uint16_t **addr,
               Size len[2],
               Index low[2])

{
  Coord min[2] = { +CoordMax, +CoordMax };
  Coord max[2] = { -CoordMax, -CoordMax };
  Coord B[4][3];
  Coord p[4][4], q[4][4];
  Size l[2], h[2], v[2];
  Image dst;
  Status status;

  if ( argcheck( series == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( img == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return exception( E_ARGVAL );

  TomotiltImage *tilt = series->tilt->tiltimage;
  Tomogeom *geom = series->geom;
  TomodataDscr *dscr = series->data->dscr;
  Size selected = 0;

  for ( Size index = 0; index < series->tilt->images; index++, tilt++, geom++, dscr++ ) {

    if ( SelectExclude( series->selection, series->exclusion, tilt->number ) ) {

      status = TomoseriesVolumeGeom( geom, dscr, series->sampling, B, v );
      if ( exception( status ) ) return status;

      TomoseriesMax( B, nz, 0,    0,    min, max );
      TomoseriesMax( B, nz, v[0], 0,    min, max );
      TomoseriesMax( B, nz, v[0], v[1], min, max );
      TomoseriesMax( B, nz, 0,    v[1], min, max );

      selected++;

    }

  }

  Coord px = Floor( min[0] );
  Coord py = Floor( min[1] );

  if ( ( px > 0 ) || ( py > 0 ) ) return exception( E_TOMOSERIES );

  Coord qx = Ceil( max[0] - px );
  Coord qy = Ceil( max[1] - py );

  Size nx = ( qx < 0 ) ? 0 : qx;
  Size ny = ( qy < 0 ) ? 0 : qy;

  Size n = nx * ny;

  if ( !n ) return exception( E_TOMOSERIES_VOL );

  uint16_t *buf = malloc( n * sizeof(*buf) );
  if ( buf == NULL ) return exception( E_MALLOC );
  memset( buf, 0, n * sizeof(*buf) );

  Coord zl = -(Coord)( nz / 2 );
  Coord zh = zl + nz - 1;

  tilt = series->tilt->tiltimage;
  geom = series->geom;
  dscr = series->data->dscr;

  for ( Size index = 0; index < series->tilt->images; index++, tilt++, geom++, dscr++ ) {

    if ( SelectExclude( series->selection, series->exclusion, tilt->number ) ) {

      status = TomoseriesVolumeGeom( geom, dscr, series->sampling, B, v );
      if ( exception( status ) ) goto error1;

      status = TomoseriesPar( B, v, zl, p );
      if ( exception( status ) ) goto error1;

      if ( nz ) {
        status = TomoseriesPar( B, v, zh, q );
        if ( exception( status ) ) goto error1;
      }

      uint16_t *b = buf;
      for ( Size iy = 0; iy < ny; iy++ ) {
        Coord y = py + iy;
        for ( Size ix = 0; ix < nx; ix++ ) {
          Coord x = px + ix;
          if ( *b < UINT16_MAX ) {
            if ( TomoseriesInPar( p, x, y ) ) {
              if ( !nz || TomoseriesInPar( q, x, y ) ) (*b)++;
            }
          }
          b++;
        }
      }

    }

  }

  status = ImageMetaAlloc( 2, &dst );
  if ( exception( status ) ) goto error1;

  dst.type = TypeUint16;
  dst.attr = ImageRealspc;
  dst.len[0] = nx;
  dst.len[1] = ny;
  dst.low[0] = px;
  dst.low[1] = py;

  if ( ( len != NULL ) || ( low != NULL ) ) {

    l[0] = h[0] = -dst.low[0];
    l[1] = h[1] = -dst.low[1];

    status = TomoseriesVolumeUse( selected, dst.len, buf, l, h );
    if ( exception( status ) ) goto error2;

    if ( len != NULL ) {
      len[0] = h[0] - l[0] + 1;
      len[1] = h[1] - l[1] + 1;
    }
    if ( low != NULL ) {
      low[0] = dst.low[0] + (Index)l[0];
      low[1] = dst.low[1] + (Index)l[1];
    }

  }

  *img = dst;
  *addr = buf;

  return E_NONE;

  error2: free( dst.len ); free( dst.low );
  error1: free( buf );

  return status;

}


extern Status TomoseriesVolumeWrite
              (const Tomoseries *series,
               const Size nz,
               const char *path)

{
  char *wpath = NULL;
  Status status;

  if ( argcheck( series == NULL ) ) return pushexception( E_ARGVAL );

  if ( ( path == NULL ) || !*path ) {
    wpath = TomoseriesOutName( series, "_vol.img" );
    status = testcondition( wpath == NULL );
    if ( status ) return status;
    path = wpath;
  }

  Image img; uint16_t *vol;
  status = TomoseriesVolume( series, nz, &img, &vol, NULL, NULL );
  if ( pushexception( status ) ) goto exit;

  status = ImageioOut( path, &img, vol, NULL );
  logexception( status );

  free( img.len ); free( img.low ); free( vol );

  exit: if ( wpath != NULL ) free( wpath );

  return status;

}


static int TomoseriesPol
           (Size n,
            Coord (*p)[4],
            Coord x,
            Coord y)

{
  Size j = n - 1;

  for ( Size i = 0; i < n; i++ ) {

    Coord s = TomoseriesLine( p[j], p[i], x, y );

    if ( s == 0 ) return j;

    if ( s > 0 ) {
      if ( p[j][3] <= 0 ) return n;
    } else {
      if ( p[j][3] >= 0 ) return n;
    }

    j = i;

  }

  return -1;

}


static Status TomoseriesVer
              (Coord B[4][3],
               Size v[2],
               Coord z,
               Size *n,
               Coord (**p)[4])

{
  Coord q[4][3];

  q[0][2] = z; TomoseriesPoint( B, 0,    0,    q[0] );
  q[1][2] = z; TomoseriesPoint( B, v[0], 0,    q[1] );
  q[2][2] = z; TomoseriesPoint( B, v[0], v[1], q[2] );
  q[3][2] = z; TomoseriesPoint( B, 0,    v[1], q[3] );

  TomoseriesPol( *n, *p, q[0][0], q[0][1] );
  TomoseriesPol( *n, *p, q[1][0], q[1][1] );
  TomoseriesPol( *n, *p, q[2][0], q[2][1] );
  TomoseriesPol( *n, *p, q[3][0], q[3][1] );

  return E_NONE;

}


extern Status TomoseriesVolumeMax
              (const Tomoseries *series,
               const Size nz,
               Size len[2],
               Index low[2])

{
  Coord B[4][3];
  Size v[2];
  Status status;

  if ( argcheck( series == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( len == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( low == NULL ) ) return exception( E_ARGVAL );

  TomotiltImage *tilt = series->tilt->tiltimage;
  Tomogeom *geom = series->geom;
  TomodataDscr *dscr = series->data->dscr;

  Coord zl = -(Coord)( nz / 2 );
  Coord zh = zl + nz - 1;

  Size r = series->tilt->param.cooref;
  status = TomoseriesVolumeGeom( geom + r, dscr + r, series->sampling, B, v );
  if ( exception( status ) ) return status;

  Size n = 4;
  Coord (*p)[4] = malloc( n * 4 * sizeof(Coord) );
  if ( p == NULL ) return exception( E_MALLOC );

  status = TomoseriesPar( B, v, zl, p );
  if ( exception( status ) ) goto error;

  for ( Size index = 0; index < series->tilt->images; index++, tilt++, geom++, dscr++ ) {

    if ( SelectExclude( series->selection, series->exclusion, tilt->number ) ) {

      status = TomoseriesVolumeGeom( geom, dscr, series->sampling, B, v );
      if ( exception( status ) ) goto error;

      status = TomoseriesVer( B, v, zl, &n, &p );
      if ( exception( status ) ) goto error;

      status = TomoseriesVer( B, v, zh, &n, &p );
      if ( exception( status ) ) goto error;

    }

  }

  len[0] = len[1] = 0;
  low[0] = low[1] = 0;

  return E_NONE;

  error: free( p );

  return status;

}
