/*----------------------------------------------------------------------------*
*
*  tomowindowcorrflt.c  -  align: image windows
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomowindow.h"
#include "array.h"
#include "convol.h"
#include "exception.h"
#include "mathdefs.h"
#include <stdlib.h>
#include <string.h>


/* functions */

#define maxkrn 9
#define maxbox ( maxkrn + maxkrn/2 + maxkrn/2)

extern Status TomowindowCorrFlt
              (const Size dim,
               const Size *len,
               const Coord *pos,
               Real *addr,
               Size krn)

{
  Real src[maxbox*maxbox];
  Real dst[maxbox*maxbox];
  Status status;

  if ( dim != 2 ) return exception( E_TOMOWINDOW );

  if ( ( len[0] < maxbox ) || ( len[1] < maxbox ) ) return E_NONE;

  if ( !krn ) return E_NONE;
  if ( krn > maxkrn ) krn = maxkrn;
  Size krnlen[2] = { krn, krn };

  if ( krn < 3 ) krn = 3;
  Size krn2 = krn / 2;
  Size box = krn + 2 * krn2;
  Size box2 = box / 2;

  Coord p0 = len[0] - box2;
  Coord p1 = len[1] - box2;
  if ( pos != NULL ) {
    p0 += Fmod( pos[0], len[0] ); if ( p0 < 0 ) p0 += len[0];
    p1 += Fmod( pos[1], len[1] ); if ( p1 < 0 ) p1 += len[1];
  }

  Size ori[2] = { p0, p1 };
  Size cut[2] = { box, box };
  Real *ptr = src;

  status = ArrayCutCyc( 2, len, addr, ori, cut, ptr, sizeof(Real) );
  if ( exception( status ) ) return status;

  if ( krnlen[0] > 1 ) {
    Real krnadr[maxkrn*maxkrn];
    status = FilterMedian2dReal( cut, ptr, krnlen, krnadr, dst );
    if ( exception( status ) ) return status;
    ptr = dst;
  }

  Real p = ptr[ box2 * box + box2 ] = -RealMax;
  for ( Size iy = box2 - krn2; iy < box2 - krn2 + krn; iy++ ) {
    for ( Size ix = box2 - krn2; ix < box2 - krn2 + krn; ix++ ) {
      Real pxy = ptr[ iy * box + ix ];
      if ( pxy > p ) p = pxy;
    }
  }
  ptr[ box2 * box + box2 ] = p;

  Size low[2] = { box2 - krnlen[0]/2, box2 - krnlen[1]/2 };
  ori[0] += low[0]; ori[1] += low[1]; 
  status = ArrayCutPasteCyc( 2, cut, ptr, low, krnlen, ori, len, addr, sizeof(Real) );
  if ( exception( status ) ) return status;

  return E_NONE;

}

extern Status TomowindowCorrMedian
              (const Size dim,
               const Size *len,
               Real *addr,
               Real *temp,
               Size krn)

{
  Real *buf = NULL;
  Status status;

  if ( dim != 2 ) return exception( E_TOMOWINDOW );

  if ( krn < 2 ) return E_NONE;
  if ( krn > maxkrn ) krn = maxkrn;

  Size klen[2] = { krn, krn };
  Real kadr[maxkrn*maxkrn];

  Size size = len[0] * len[1] * sizeof(Real);
  if ( temp == NULL ) {
    buf = malloc( size );
    if ( buf == NULL ) return exception( E_MALLOC );
    temp = buf;
  }

  status = FilterMedian2dReal( len, addr, klen, kadr, temp );
  if ( exception( status ) ) goto exit;

  memcpy( addr, temp, size );

  exit: if ( buf != NULL ) free( buf );

  return E_NONE;

}
