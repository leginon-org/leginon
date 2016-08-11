/*----------------------------------------------------------------------------*
*
*  imagesumabs2.c  -  image: array operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagearraycommon.h"
#include "exception.h"
#include "mathdefs.h"


/* macros */

#define PosReal( src, dst )                                                  \
  {                                                                          \
    Real s = src, *d = dst;                                                  \
    *d += s * s;                                                             \
  }                                                                          \

#define PosCmplx( src, dst )                                                 \
  {                                                                          \
    Cmplx s = src; Real *d = dst;                                            \
    Real re = Re( s ), im = Im( s );                                         \
    *d += re * re + im * im;                                                 \
  }                                                                          \


/* functions */

static Status SumAbs2Asym
              (Type type,
               Size srclen,
               const void *srcpos,
               const void *srcneg,
               Size dstlen,
               void *dst)

{

  switch ( type ) {
    case TypeReal:
    case TypeImag:  FnAsymS( Real,  Real, PosReal  ); break;
    case TypeCmplx: FnAsymS( Cmplx, Real, PosCmplx ); break;
    default: return exception( E_IMAGE_TYPE );
  }

  return E_NONE;

}


static Status SumAbs2Sym
              (Type type,
               Size srclen,
               const void *srcpos,
               const void *srcneg,
               Size dstlen,
               void *dst)

{

  switch ( type ) {
    case TypeReal:
    case TypeImag:  FnSymS( Real,  Real, PosReal,  PosReal  ); break;
    case TypeCmplx: FnSymS( Cmplx, Real, PosCmplx, PosCmplx ); break;
    default: return exception( E_IMAGE_TYPE );
  }

  return E_NONE;

}


extern Status ImageSumAbs2
              (const Image *src,
               const void *srcaddr,
               void *dstaddr)

{
  static const ImageFnTab fntab = {
    SumAbs2Asym,
    SumAbs2Sym,
    SumAbs2Sym,
    SumAbs2Sym,
    SumAbs2Sym,
  };

  Real *daddr = dstaddr;

  *daddr = 0;

  return exception( ImageFnsExec( &fntab, src, srcaddr, dstaddr ) );

}
