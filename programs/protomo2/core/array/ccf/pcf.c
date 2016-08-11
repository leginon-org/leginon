/*----------------------------------------------------------------------------*
*
*  pcf.c  -  array: phase-only cross-correlation function
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

extern Status PCFReal
              (Size count,
               const Real *src0,
               const Real *src1,
               Real *dst)

{

  while ( count-- ) {

    Real re0 = *src0++;
    Real re1 = *src1++;

    if ( re0 > 0 ) {

      if ( re1 > 0 ) {
        *dst++ = 1;
      } else if ( re1 < 0 ) {
        *dst++ = -1;
      } else {
        *dst++ = 0;
      }

    } else if ( re0 < 0 ) {

      if ( re1 > 0 ) {
        *dst++ = -1;
      } else if ( re1 < 0 ) {
        *dst++ = 1;
      } else {
        *dst++ = 0;
      }

    } else {

      *dst++ = 0;

    }

  }

  return E_NONE;

}


extern Status PCFImag
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

    if ( im0 > 0 ) {

      if ( im1 > 0 ) {
        *dst++ = 1;
      } else if ( im1 < 0 ) {
        *dst++ = -1;
      } else {
        *dst++ = 0;
      }

    } else if ( im0 < 0 ) {

      if ( im1 > 0 ) {
        *dst++ = -1;
      } else if ( im1 < 0 ) {
        *dst++ = 1;
      } else {
        *dst++ = 0;
      }

    } else {

      *dst++ = 0;

    }

  }

  return E_NONE;

}


extern Status PCFCmplx
              (Size count,
               const Cmplx *src0,
               const Cmplx *src1,
               Cmplx *dst)

{

  while ( count-- ) {

    Real re0 = Re( *src0 ), im0 = Im( *src0 ), abs0 = FnSqrt( re0 * re0 + im0 * im0 );
    Real re1 = Re( *src1 ), im1 = Im( *src1 ), abs1 = FnSqrt( re1 * re1 + im1 * im1 );

    if ( ( abs0 > 0 ) && ( abs1 > 0 ) ) {

      re0 /= abs0; im0 /= abs0;
      re1 /= abs1; im1 /= abs1;

      Real re = re0 * re1 + im0 * im1;
      Real im = re0 * im1 - re1 * im0;

      Cset( *dst, re, im );

    } else {

      Cset( *dst, 0, 0 );

    }

    dst++; src0++; src1++;

  }

  return E_NONE;

}
