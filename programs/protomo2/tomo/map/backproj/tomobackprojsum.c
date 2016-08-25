/*----------------------------------------------------------------------------*
*
*  tomobackprojsum.c  -  map: weighted backprojection
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomobackproj.h"
#include "tomomapcommon.h"
#include "thread.h"
#include "exception.h"
#include "message.h"
#include <stdlib.h>
#include <string.h>


/* functions */

static Status TomobackprojInterp
              (const Tomoproj *proj,
               const Size iz,
               const Size dstlen[3],
               const Index dstlow[3],
               Real *dst)

{
  Coord tol = ArrayCoordTol / 2;
  Status status = E_NONE;

  const Size *srclen = proj->len;
  const Real *src = proj->img;

  Coord a00 = proj->A[0][0], a01 = proj->A[0][1];
  Coord a10 = proj->A[1][0], a11 = proj->A[1][1];
  Coord a20 = proj->A[2][0], a21 = proj->A[2][1];

  Coord z = iz; z += dstlow[2];
  Coord z0 = a20 * z + proj->b[0];
  Coord z1 = a21 * z + proj->b[1];

  for ( Size iy = 0; iy < dstlen[1]; iy++ ) {
    Coord y = iy; y += dstlow[1];
    Coord y0 = a10 * y + z0;
    Coord y1 = a11 * y + z1;

    for ( Size ix = 0; ix < dstlen[0]; ix++ ) {
      Coord x = ix; x += dstlow[0];
      Coord x0 = a00 * x + y0;
      Coord x1 = a01 * x + y1;

      Coord x0i = Floor( x0 );
      Coord x0d = x0 - x0i;

      Coord x1i = Floor( x1 );
      Coord x1d = x1 - x1i;

      Size i0, i1;
      Size j0, j1;

      if ( x0i < 0 ) goto clip;
      i0 = x0i;
      if ( x0d < tol ) {
        j0 = i0;
        x0d = 0;
      } else {
        j0 = i0 + 1;
      }
      if ( j0 >= srclen[0] ) goto clip;

      if ( x1i < 0 ) goto clip;
      i1 = x1i;
      if ( x1d < tol ) {
        j1 = i1;
        x1d = 0;
      } else {
        j1 = i1 + 1;
      }
      if ( j1 >= srclen[1] ) goto clip;

      Coord dstval = ( 1 - x0d ) * ( ( 1 - x1d ) * src[ i0 + i1 * srclen[0] ] + x1d * src[ i0 + j1 * srclen[0] ] )
                   +       x0d   * ( ( 1 - x1d ) * src[ j0 + i1 * srclen[0] ] + x1d * src[ j0 + j1 * srclen[0] ] );

      *dst++ += dstval;
      continue;

      clip:
      dst++;
      status = E_TOMOBACKPROJ_CLIP;

    } /* end for ix */

  } /* end for iy */

  return status;

}


static Status TomobackprojSumExec
              (Size thread,
               const void *inarg,
               void *outarg)

{
  Tomocomp *comp = outarg;
  Status status = E_NONE;

  if ( comp->map->flags & TomoMsg ) {
    Coord z = thread; z += comp->low[2];
    MessageFormat( "z = %"CoordG"\n", z  );
  }

  Size len = comp->len[0] * comp->len[1];
  Size size = len * sizeof(Real);
  Offset offs = len * thread;
  Real *addr;

  if ( comp->handle == NULL ) {

    addr = comp->addr + offs;

  } else {

    addr = malloc( size );
    if ( addr == NULL ) return exception( E_MALLOC );

  }

  memset( addr, 0, size );

  const Tomoproj *proj = comp->map->proj;

  for ( Size i = 0; i < comp->map->count; i++, proj++ ) {

    if ( TomobackprojInterp( proj, thread, comp->len, comp->low, addr ) ) status = E_TOMOBACKPROJ_CLIP;

  }

  if ( comp->handle != NULL ) {

    status = TomoioWrite( comp->handle, offs * sizeof(Real), size, addr );
    if ( exception( status ) ) return status;

    free( addr );

  }

  return E_NONE;

}


extern Status TomobackprojSum
              (Tomocomp *comp)

{
  Status status;

  if ( comp->map->flags & TomoLog ) {
    Message( "backprojecting...", "\n" );
  }

  Thread *thread = malloc( comp->len[2] * sizeof(Thread) );
  if ( thread == NULL ) return exception( E_MALLOC );

  for ( Size t = 0; t < comp->len[2]; t++ ) {
    thread[t].function = TomobackprojSumExec;
    thread[t].inarg = NULL;
    thread[t].outarg = comp;
  }

  if ( comp->map->flags & TomoMsg ) {
    MessageFormat( "%"SizeU" map sections\n", comp->len[2] );
  }

  status = ThreadExec( comp->len[2], thread );
  if ( status == E_THREAD_ERROR ) {
    logexception( status ); goto exit;
  } else if ( status ) {
    pushexception( status ); goto exit;
  }

  if ( comp->map->flags & TomoLog ) {
    Message( "end backprojecting.", "\n" );
  }

  exit: free( thread );

  return status;

}
