/*----------------------------------------------------------------------------*
*
*  tomorefmrg.c  -  align: reference
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomorefcommon.h"
#include "mat3.h"
#include "exception.h"
#include "macros.h"
#include <string.h>


/* functions */

static void TomorefMrgTrf
            (const TomorefImage *refimage,
             const WindowFourier *window,
             Coord A1i[3][3],
             Coord Sj[3][3],
             Coord *n,
             Cmplx *refaddr,
             Size sampling,
             Coord dz)

{
  const Image *img = &window->img;
  const Image *fou = &window->fou;
  Coord A[3][3];

  /* reciprocal space width and sigma */
  Coord w = 1 / dz;
  Coord s = w / 100;
  /* for filter generation */
  Coord t = 2 * s / w;
  /* units */
  Coord u0 = 2 / ( sampling * img->len[0] * w );
  Coord u1 = 2 / ( sampling * img->len[1] * w );

  Real *ref = (Real *)refaddr;
  Real *R = (Real *)refimage->transform;

  /* direct space basis transformation: Sj -> Ij -> O -> Ii */
  /* direct space transformation matrix: (Ai)-1(Aj)(A''j)-1 */
  /* reciprocal space coordinate transform is the same then */
  Mat3Mul( A1i, Sj, A );

  /* width in z and units; need only this row of matrix (z coo) */
  Coord a0 = u0 * A[2][0];
  Coord a1 = u1 * A[2][1];

  /* mask out a slice of width 1/Dz */
  for ( Size iy = 0; iy < fou->len[1]; iy++ ) {
    Coord y = iy; y += fou->low[1];
    Coord zy = a1 * y;

    for ( Size ix = 0; ix < fou->len[0]; ix++ ) {
      Coord x = ix; x += fou->low[0];
      Coord zx = a0 * x;

      Coord z = Fabs( zx + zy );
      Coord f = ( Erf( ( z + 1 ) / t ) - Erf( ( z - 1 ) / t ) ) / 2;
      *ref++ += f * *R++;
      *ref++ += f * *R++;
      *n++  += f;

    } /* end for ix */

  } /* end for iy */

}


extern Status TomorefMrgTransform
              (const Tomoref *ref,
               Size refindex,
               Cmplx *addr,
               Coord *n,
               Coord dz)

{
  Size index;

  const TomorefImage *refimage = ref->refimage;
  Size cooref = ref->image->cooref;
  if ( refindex == cooref ) return pushexception( E_TOMOREF );

  const Tomoimage *image = ref->image;
  TomoimageList *list = image->list;
  const WindowFourier *window = ref->fourier;
  Size fousize = window->fousize;

  memset( addr, 0, fousize * sizeof(Cmplx) );
  memset( n, 0, fousize * sizeof(Coord) );

  Coord (*A1i)[3] = list[refindex].A1;
  Coord sampling = ref->series->sampling;
  TomorefMrgTrf( refimage + cooref, window, A1i, list[cooref].S, n, addr, sampling, dz );

  Size count = MIN( ref->mincount, ref->maxcount );

  for ( index = 0; index < count; index++ ) {

    Size min = image->min[index];
    if ( ( index != refindex  ) && ( min < SizeMax ) && ( list[min].flags & TomoimageRef ) ) {
      TomorefMrgTrf( refimage + min, window, A1i, list[min].S, n, addr, sampling, dz );
    }

    Size max = image->max[index];
    if ( ( index != refindex  ) && ( max < SizeMax ) && ( list[max].flags & TomoimageRef ) ) {
      TomorefMrgTrf( refimage + max, window, A1i, list[max].S, n, addr, sampling, dz );
    }

  }

  if ( index < ref->mincount ) {
    Size min = image->min[index];
    if ( ( index != refindex  ) && ( min < SizeMax ) && ( list[min].flags & TomoimageRef ) ) {
      TomorefMrgTrf( refimage + min, window, A1i, list[min].S, n, addr, sampling, dz );
    }
    if ( index + 1 != ref->mincount ) return pushexception( E_TOMOREF );
  }

  if ( index < ref->maxcount ) {
    Size max = image->max[index];
    if ( ( index != refindex  ) && ( max < SizeMax ) && ( list[max].flags & TomoimageRef ) ) {
      TomorefMrgTrf( refimage + max, window, A1i, list[max].S, n, addr, sampling, dz );
    }
    if ( index + 1 != ref->maxcount ) return pushexception( E_TOMOREF );
  }

  for ( Size i = 0; i < fousize; i++ ) {
    if ( n[i] > 1 ) {
      Cset( addr[i], Re( addr[i] ) / n[i], Im( addr[i] ) / n[i] );
    }
  }

  return E_NONE;

}
