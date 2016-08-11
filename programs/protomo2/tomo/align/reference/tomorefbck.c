/*----------------------------------------------------------------------------*
*
*  tomorefbck.c  -  align: reference
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
#include "exception.h"
#include "macros.h"
#include <string.h>


/* functions */

static void TomorefBckTrf
            (const TomorefImage *refimage,
             const WindowFourier *window,
             Coord Si[3][3],
             Coord A1j[3][3],
             Real *sinc,
             Cmplx *refaddr,
             const TomotransferParam *param)

{
  const Image *fou = &window->fou;
  Size fousize = window->fousize;

  memset( sinc, 0, fousize * sizeof(Real) );
  TomotransferAdd( fou->len, fou->low, Si, A1j, sinc, param );

  Real *ref = (Real *)refaddr;
  Real *R = (Real *)refimage->transform;
  Real *H = refimage->transfer;
  Coord thr2 = param->bthr * param->bthr;

  for ( Size k = 0; k < fousize; k++ ) {
    /* thresholded transfer function */
    Coord h = H[k];
    h = Sqrt( h * h + thr2 );
    if ( H[k] < 0 ) h = -h;
    /* weighting and reprojection */
    Real w = sinc[k] / h;
    *ref++ += w * *R++;
    *ref++ += w * *R++;
  }

}


extern Status TomorefBckTransform
              (const Tomoref *ref,
               Size refindex,
               Cmplx *addr,
               Real *sinc,
               const TomotransferParam *param)

{
  Coord Si[3][3];
  Size index;

  const TomorefImage *refimage = ref->refimage;
  Size cooref = ref->image->cooref;
  if ( refindex == cooref ) return pushexception( E_TOMOREF );

  const Tomoimage *image = ref->image;
  TomoimageList *list = image->list;
  const WindowFourier *window = ref->fourier;

  TomotransferScale( list[refindex].S, ref->series->sampling, window->img.len, Si );

  memset( addr, 0, window->fousize * sizeof(Cmplx) );
  TomorefBckTrf( refimage + cooref, window, Si, list[cooref].A1, sinc, addr, param );

  Size count = MIN( ref->mincount, ref->maxcount );

  for ( index = 0; index < count; index++ ) {

    Size min = image->min[index];
    if ( ( index != refindex  ) && ( min < SizeMax ) && ( list[min].flags & TomoimageRef ) ) {
      TomorefBckTrf( refimage + min, window, Si, list[min].A1, sinc, addr, param );
    }

    Size max = image->max[index];
    if ( ( index != refindex  ) && ( max < SizeMax ) && ( list[max].flags & TomoimageRef ) ) {
      TomorefBckTrf( refimage + max, window, Si, list[max].A1, sinc, addr, param );
    }

  }

  if ( index < ref->mincount ) {
    Size min = image->min[index];
    if ( ( index != refindex  ) && ( min < SizeMax ) && ( list[min].flags & TomoimageRef ) ) {
      TomorefBckTrf( refimage + min, window, Si, list[min].A1, sinc, addr, param );
    }
    if ( index + 1 != ref->mincount ) return pushexception( E_TOMOREF );
  }

  if ( index < ref->maxcount ) {
    Size max = image->max[index];
    if ( ( index != refindex  ) && ( max < SizeMax ) && ( list[max].flags & TomoimageRef ) ) {
      TomorefBckTrf( refimage + max, window, Si, list[max].A1, sinc, addr, param );
    }
    if ( index + 1 != ref->maxcount ) return pushexception( E_TOMOREF );
  }

  return E_NONE;

}
