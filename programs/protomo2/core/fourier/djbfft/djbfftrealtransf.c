/*----------------------------------------------------------------------------*
*
*  djbfftrealtransf.c  -  djbfft: fast Fourier transforms
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "djbfftcommon.h"
#include "exception.h"
#include "mathdefs.h"
#include <stdlib.h>
#include <string.h>


/* functions */

static Status RealTransf1
              (Size n[1],
               const Real *src,
               Cmplx *dst,
               Size count,
               Cmplx *tmp,
               FourierOpt opt,
               DJBfftData *data)

{
  Real *rtmp = (Real *)tmp;

  while ( count-- ) {

    DJBpackReal( n[0], src, rtmp, data[0].scale );

    data[0].fr( rtmp );

    DJBforwPosReal( n[0], rtmp, (Real *)dst, data[0].rtab );

    if ( opt & FourierSetZeroorig ) {
      Cset( *dst, 0, 0 );
    }

    src += n[0];
    dst += n[0] / 2 + 1;

  }

  return E_NONE;

}


static Status RealTransf2
              (Size n[2],
               const Real *src,
               Cmplx *dst,
               Size count,
               Cmplx *tmp,
               FourierOpt opt,
               DJBfftData *data)

{
  Size n0inc = n[0] / 2 + 1;

  Real *rtmp = (Real *)tmp;

  while ( count-- ) {

    Cmplx *dst0 = dst;

    for ( Size i = 0; i < n[1];  i++ ) {

      DJBpackReal( n[0], src, rtmp, data[0].scale );

      data[0].fr( rtmp );

      DJBforwPosReal( n[0], rtmp, (Real *)dst, data[0].rtab );

      src += n[0];
      dst += n0inc;

    }

    Cmplx *dst1 = dst0;

    DJBpackReal2( n[1], (Real *)dst1, 2 * n0inc, rtmp );

    data[1].fr( rtmp );

    DJBforwPosReal2( n[1], rtmp, (Real *)dst1, 2 * n0inc, data[1].rtab );

    FourierExtCmplxHerm( n[1], dst1++, n0inc );

    for ( Size i = 1; i < n[0] / 2;  i++ ) {

      FourierPosCmplx2( n[1], dst1, n0inc, tmp, 1 );

      data[1].fc( tmp );

      DJBforwPosCmplx2( n[1], tmp, dst1++, n0inc, data[1].ctab );

    }

    DJBpackReal2( n[1], (Real *)dst1, 2 * n0inc, rtmp );

    data[1].fr( rtmp );

    DJBforwPosReal2( n[1], rtmp, (Real *)dst1, 2 * n0inc, data[1].rtab );

    FourierExtCmplxHerm( n[1], dst1, n0inc );

    if ( opt & FourierSetZeroorig ) {
      Cset( *dst0, 0, 0 );
    }

    if ( opt & FourierDoCenter ) {
      FourierCenterSymCmplx( 2, n, dst0, dst0 );
    }

  }

  return E_NONE;

}


static Status RealTransf3
              (Size n[3],
               const Real *src,
               Cmplx *dst,
               Size count,
               Cmplx *tmp,
               FourierOpt opt,
               DJBfftData *data)

{
  Status status;

  Size n0inc = n[0] / 2 + 1;

  while ( count-- ) {

    status = RealTransf2( n, src, dst, n[2], tmp, 0, data );
    if ( exception( status ) ) return status;

    for ( Size i = 0; i < n0inc * n[1];  i++ ) {

      FourierPosCmplx2( n[2], dst + i, n0inc * n[1], tmp, 1 );

      data[2].fc( tmp );

      DJBforwPosCmplx2( n[2], tmp, dst + i, n0inc * n[1], data[2].ctab );

    }

    if ( opt & FourierSetZeroorig ) {
      Cset( *dst, 0, 0 );
    }

    if ( opt & FourierDoCenter ) {
      FourierCenterSymCmplx( 3, n, dst, dst );
    }

    src += n[2] * n[1] * n[0];
    dst += n[2] * n[1] * n0inc;

  }

  return E_NONE;

}




extern Status DJBfftRealTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count)

{
  DJBfftData *data = fou->data;
  void *tmp = data[0].tmp;
  Status status;

  switch ( fou->dim ) {
    case 0:  status = exception( E_ARGVAL ); break;
    case 1:  status = exception( RealTransf1( fou->len, src, dst, count, tmp, fou->opt, data ) ); break;
    case 2:  status = exception( RealTransf2( fou->len, src, dst, count, tmp, fou->opt, data ) ); break;
    case 3:  status = exception( RealTransf3( fou->len, src, dst, count, tmp, fou->opt, data ) ); break;
    default: status = exception( E_FOURIER_DIM );
  }

  return status;

}



static Status ImagTransf1
              (Size n[1],
               const Imag *src,
               Cmplx *dst,
               Size count,
               Cmplx *tmp,
               FourierOpt opt,
               DJBfftData *data)

{
  Real *rtmp = (Real *)tmp;

  while ( count-- ) {

    DJBpackReal( n[0], (const Real *)src, rtmp, data[0].scale );

    data[0].fr( rtmp );

    DJBforwMulIReal( n[0], rtmp, (Real *)dst, data[0].rtab );

    if ( opt & FourierSetZeroorig ) {
      Cset( *dst, 0, 0 );
    }

    src += n[0];
    dst += n[0] / 2 + 1;

  }

  return E_NONE;

}


static Status ImagTransf2
              (Size n[2],
               const Imag *src,
               Cmplx *dst,
               Size count,
               Cmplx *tmp,
               FourierOpt opt,
               DJBfftData *data)

{
  Size n0inc = n[0] / 2 + 1;

  Real *rtmp = (Real *)tmp;

  while ( count-- ) {

    Cmplx *dst0 = dst;

    for ( Size i = 0; i < n[1];  i++ ) {

      DJBpackReal( n[0], (const Real *)src, rtmp, data[0].scale );

      data[0].fr( rtmp );

      DJBforwPosReal( n[0], rtmp, (Real *)dst, data[0].rtab );

      src += n[0];
      dst += n0inc;

    }

    Cmplx *dst1 = dst0;

    DJBpackReal2( n[1], (Real *)dst1, 2 * n0inc, rtmp );

    data[1].fr( rtmp );

    DJBforwMulIReal2( n[1], rtmp, (Real *)dst1, 2 * n0inc, data[1].rtab );

    FourierExtCmplxAHerm( n[1], dst1++, n0inc );

    for ( Size i = 1; i < n[0] / 2;  i++ ) {

      FourierPosCmplx2( n[1], dst1, n0inc, tmp, 1 );

      data[1].fc( tmp );

      DJBforwMulICmplx2( n[1], tmp, dst1++, n0inc, data[1].ctab );

    }

    DJBpackReal2( n[1], (Real *)dst1, 2 * n0inc, rtmp );

    data[1].fr( rtmp );

    DJBforwMulIReal2( n[1], rtmp, (Real *)dst1, 2 * n0inc, data[1].rtab );

    FourierExtCmplxAHerm( n[1], dst1, n0inc );

    if ( opt & FourierSetZeroorig ) {
      Cset( *dst0, 0, 0 );
    }

    if ( opt & FourierDoCenter ) {
      FourierCenterSymCmplx( 2, n, dst0, dst0 );
    }

  }

  return E_NONE;

}


static Status ImagTransf3
              (Size n[3],
               const Imag *src,
               Cmplx *dst,
               Size count,
               Cmplx *tmp,
               FourierOpt opt,
               DJBfftData *data)

{
  Status status;

  Size n0inc = n[0] / 2 + 1;

  while ( count-- ) {

    status = RealTransf2( n, (const Real *)src, dst, n[2], tmp, 0, data );
    if ( exception( status ) ) return status;

    for ( Size i = 0; i < n0inc * n[1];  i++ ) {

      FourierPosCmplx2( n[2], dst + i, n0inc * n[1], tmp, 1 );

      data[2].fc( tmp );

      DJBforwMulICmplx2( n[2], tmp, dst + i, n0inc * n[1], data[2].ctab );

    }

    if ( opt & FourierSetZeroorig ) {
      Cset( *dst, 0, 0 );
    }

    if ( opt & FourierDoCenter ) {
      FourierCenterSymCmplx( 3, n, dst, dst );
    }

    src += n[2] * n[1] * n[0];
    dst += n[2] * n[1] * n0inc;

  }

  return E_NONE;

}




extern Status DJBfftImagTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count)

{
  DJBfftData *data = fou->data;
  void *tmp = data[0].tmp;
  Status status;

  switch ( fou->dim ) {
    case 0:  status = exception( E_ARGVAL ); break;
    case 1:  status = exception( ImagTransf1( fou->len, src, dst, count, tmp, fou->opt, data ) ); break;
    case 2:  status = exception( ImagTransf2( fou->len, src, dst, count, tmp, fou->opt, data ) ); break;
    case 3:  status = exception( ImagTransf3( fou->len, src, dst, count, tmp, fou->opt, data ) ); break;
    default: status = exception( E_FOURIER_DIM );
  }

  return status;

}


