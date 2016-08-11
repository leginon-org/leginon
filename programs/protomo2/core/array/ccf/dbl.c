/*----------------------------------------------------------------------------*
*
*  dbl.c  -  array: phase doubled cross-correlation function
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "ccf.h"
#include "exception.h"
#include "mathdefs.h"


/* functions */

extern Status DBLReal
              (Size count,
               const Real *src0,
               const Real *src1,
               Real *dst)

{

  while ( count-- ) {

    Real re0 = *src0++;
    Real re1 = *src1++;

    *dst++ = FnFabs( re0 * re1 );

  }

  return E_NONE;

}


extern Status DBLImag
              (Size count,
               const Imag *src0,
               const Imag *src1,
               Real *dst)

{
  const Real *s0 = (Real *)src0;
  const Real *s1 = (Real *)src1;

  while ( count-- ) {

    Real im0 = *s0++;
    Real im1 = *s1++;

    *dst++ = FnFabs( im0 * im1 );

  }

  return E_NONE;

}


extern Status DBLCmplx
              (Size count,
               const Cmplx *src0,
               const Cmplx *src1,
               Cmplx *dst)

{

  while ( count-- ) {

    Real re0 = Re( *src0 ), im0 = Im( *src0 );
    Real re1 = Re( *src1 ), im1 = Im( *src1 );

    Real re = re0 * re1 + im0 * im1;
    Real im = re0 * im1 - re1 * im0;

    Real re2 = re * re;
    Real im2 = im * im;

    Real dstabs = FnSqrt( re2 + im2 );
    if ( dstabs > 0 ) {
      Cset( *dst, ( re2 - im2 ) / dstabs, 2 * re * im / dstabs );
    } else {
      Cset( *dst, 0, 0 );
    }

    dst++; src0++; src1++;

  }

  return E_NONE;

}
