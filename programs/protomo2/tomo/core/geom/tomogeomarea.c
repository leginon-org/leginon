/*----------------------------------------------------------------------------*
*
*  tomogeomarea.c  -  tomography: tilt geometry
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
#include "baselib.h"
#include "mat3.h"
#include "exception.h"


/* functions */

static void TomogeomPointMax
            (Coord A[3][3],
             Coord a[2],
             Coord x,
             Coord y,
             Coord z,
             Coord *rmin,
             Coord *rmax)

{
  Coord r[3];

  r[0] = x; r[1] = y; r[2] = z;

  Mat3TranspMulVec( A, r, r );

  r[0] += a[0];
  r[1] += a[1];

  if ( r[0] < rmin[0] ) rmin[0] = r[0];
  if ( r[1] < rmin[1] ) rmin[1] = r[1];

  if ( r[0] > rmax[0] ) rmax[0] = r[0];
  if ( r[1] > rmax[1] ) rmax[1] = r[1];

}


extern Status TomogeomAreaMax
              (Size nx,
               Size ny,
               Size nz,
               Coord A[3][3],
               Coord a[2],
               Size *len,
               Size *ori,
               Size *size)

{

  if ( argcheck( A == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( a == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( len == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( ori == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( size == NULL ) ) return exception( E_ARGVAL );

  Coord min[3] = { +CoordMax, +CoordMax, +CoordMax };
  Coord max[3] = { -CoordMax, -CoordMax, -CoordMax };
  Coord px, py, pz, qx, qy, qz;
  Size n;

  px = nx / 2; px = -px;
  py = ny / 2; py = -py;
  pz = nz / 2; pz = -pz;

  qx = nx ? px + ( nx - 1 ) : px;
  qy = ny ? py + ( ny - 1 ) : py;
  qz = nz ? pz + ( nz - 1 ) : pz;

  TomogeomPointMax( A, a, px, py, pz, min, max );
  TomogeomPointMax( A, a, qx, py, pz, min, max );
  TomogeomPointMax( A, a, px, qy, pz, min, max );
  TomogeomPointMax( A, a, qx, qy, pz, min, max );

  if ( qz > pz ) {

    TomogeomPointMax( A, a, px, py, qz, min, max );
    TomogeomPointMax( A, a, qx, py, qz, min, max );
    TomogeomPointMax( A, a, px, qy, qz, min, max );
    TomogeomPointMax( A, a, qx, qy, qz, min, max );

  }

  px = Floor( min[0] );
  py = Floor( min[1] );

  qx = Ceil( max[0] );
  qy = Ceil( max[1] );

  nx = ( px > qx ) ? 0 : qx - px + 1;
  ny = ( py > qy ) ? 0 : qy - py + 1;

  n = nx * ny;

  if ( px < 0 ) px = 0;
  if ( py < 0 ) py = 0;

  nx = ( px > qx ) ? 0 : qx - px + 1;
  ny = ( py > qy ) ? 0 : qy - py + 1;

  if ( !nx || !ny ) return exception( E_TOMOGEOM_AREA );

  len[0] = FactorGE2( nx, 19 );
  len[1] = FactorGE2( ny, 19 );

  while ( len[0] - nx < 4 ) len[0] = FactorGE2( len[0] + 2, 19 );
  while ( len[1] - ny < 4 ) len[1] = FactorGE2( len[1] + 2, 19 );

  ori[0] = px;
  ori[1] = py;

  *size = n;

  return E_NONE;

}
