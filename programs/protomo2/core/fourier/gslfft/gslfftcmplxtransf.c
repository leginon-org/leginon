/*----------------------------------------------------------------------------*
*
*  gslfftcmplxtransf.c  -  gslfft: fast Fourier transforms with gsl
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "gslfftcommon.h"
#include "exception.h"
#include "mathdefs.h"
#include <string.h>


/* functions */

static Status CmplxTransf1
              (Size n[1],
               const Cmplx *src,
               Cmplx *dst,
               Size count,
               void *wk[],
               FourierOpt opt,
               GSLfftData *data)

{

  if ( n[0] == 1 ) {

    if ( opt & FourierSetZeroorig ) {

      while ( count-- ) {
        Cset( *dst, 0, 0 );
        dst++;
      }

    } else {

      while ( count-- ) {
        Cset( *dst, data[0].scale * Re( *src ), data[0].scale * Im( *src ) );
        dst++; src++;
      }

    }

  } else {

    while ( count-- ) {

      if ( data[0].scale == 1.0 ) {
        memcpy( dst, src, n[0] * sizeof(Cmplx) );
      } else {
        for ( Size i = 0; i < n[0]; i++ ) {
          Cset( dst[i], data[0].scale * Re( src[i] ), data[0].scale * Im( src[i] ) );
        }
      }

      if ( gsl_fft_complex_float_forward( (float *)dst, 1, data[0].n, data[0].wtab, wk[0] ) ) {
        return exception( E_GSLFFT );
      }

      if ( opt & FourierSetZeroorig ) {
        Cset( *dst, 0, 0 );
      }

      if ( opt & FourierDoCenter ) {
        FourierCenterAsymCmplx( 1, n, dst, dst );
      }

      src += n[0];
      dst += n[0];

    }

  }

  return E_NONE;

}


static Status CmplxTransf2
              (Size n[2],
               const Cmplx *src,
               Cmplx *dst,
               Size count,
               void *wk[],
               FourierOpt opt,
               GSLfftData *data)

{
  Status status;

  while ( count-- ) {

    status = CmplxTransf1( n, src, dst, n[1], wk, 0, data );
    if ( exception( status ) ) return status;

    for ( Size i = 0; i < n[0];  i++ ) {

      if ( gsl_fft_complex_float_forward( (float *)( dst + i ), n[0], data[1].n, data[1].wtab, wk[1] ) ) {
        return exception( E_GSLFFT );
      }

    }

    if ( opt & FourierSetZeroorig ) {
      Cset( *dst, 0, 0 );
    }

    if ( opt & FourierDoCenter ) {
      FourierCenterAsymCmplx( 2, n, dst, dst );
    }

    src += n[0] * n[1];
    dst += n[0] * n[1];

  }

  return E_NONE;

}


static Status CmplxTransf3
              (Size n[3],
               const Cmplx *src,
               Cmplx *dst,
               Size count,
               void *wk[],
               FourierOpt opt,
               GSLfftData *data)

{
  Status status;

  while ( count-- ) {

    status = CmplxTransf2( n, src, dst, n[2], wk, 0, data );
    if ( exception( status ) ) return status;

    for ( Size i = 0; i < n[0] * n[1];  i++ ) {

      if ( gsl_fft_complex_float_forward( (float *)( dst + i ), n[0] * n[1], data[2].n, data[2].wtab, wk[2] ) ) {
        return exception( E_GSLFFT );
      }

    }

    if ( opt & FourierSetZeroorig ) {
      Cset( *dst, 0, 0 );
    }

    if ( opt & FourierDoCenter ) {
      FourierCenterAsymCmplx( 3, n, dst, dst );
    }

    src += n[0] * n[1] * n[2];
    dst += n[0] * n[1] * n[2];

  }

  return E_NONE;

}


extern Status GSLfftCmplxTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count)

{
  void *wk[3];
  Status status;

  status = GSLfftWk( fou->dim, fou->data, wk, sizeof(wk) );
  if ( exception( status ) ) return status;

  switch ( fou->dim ) {
    case 0:  status = exception( E_ARGVAL ); break;
    case 1:  status = exception( CmplxTransf1( fou->len, src, dst, count, wk, fou->opt, fou->data ) ); break;
    case 2:  status = exception( CmplxTransf2( fou->len, src, dst, count, wk, fou->opt, fou->data ) ); break;
    case 3:  status = exception( CmplxTransf3( fou->len, src, dst, count, wk, fou->opt, fou->data ) ); break;
    default: status = exception( E_FOURIER_DIM );
  }

  return status;

}
