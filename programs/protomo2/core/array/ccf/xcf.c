/*----------------------------------------------------------------------------*
*
*  xcf.c  -  array: conventional cross-correlation function
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

extern Status XCFReal
              (Size count,
               const Real *src0,
               const Real *src1,
               Real *dst)

{

  while ( count-- ) {

    *dst++ = *src0++ * *src1++;

  }

  return E_NONE;

}


extern Status XCFImag
              (Size count,
               const Imag *src0,
               const Imag *src1,
               Real *dst)

{
  const Real *s0 = (Real *)src0;
  const Real *s1 = (Real *)src1;

  while ( count-- ) {

    *dst++ = *s0++ * *s1++;

  }

  return E_NONE;

}


extern Status XCFCmplx
              (Size count,
               const Cmplx *src0,
               const Cmplx *src1,
               Cmplx *dst)

{

  while ( count-- ) {

    Real re0 = Re( *src0 ), im0 = Im( *src0 );
    Real re1 = Re( *src1 ), im1 = Im( *src1 );

    /* conj(src0) * src1 */
    Real re = re0 * re1 + im0 * im1;
    Real im = re0 * im1 - re1 * im0;

    Cset( *dst, re, im );

    dst++; src0++; src1++;

  }

  return E_NONE;

}
