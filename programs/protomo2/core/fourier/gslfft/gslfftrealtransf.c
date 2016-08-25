/*----------------------------------------------------------------------------*
*
*  gslfftrealtransf.c  -  gslfft: fast Fourier transforms with gsl
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

static Status RealTransf1
              (Size n[1],
               const Real *src,
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
        Cset( *dst, data[0].scale * *src, 0 );
        dst++; src++;
      }

    }

  } else {

    while ( count-- ) {

      Real *d = (Real *)dst; d++;
      if ( data[0].scale == 1.0 ) {
        memcpy( d, src, n[0] * sizeof(Real) );
      } else {
        for ( Size i = 0; i < n[0]; i++ ) {
          d[i] = data[0].scale * src[i];
        }
      }

      if ( gsl_fft_real_float_transform( (float *)d--, 1, data[0].n, data[0].wtab, wk[0] ) ) {
        return exception( E_GSLFFT );
      }
      d[0] = ( opt & FourierSetZeroorig ) ? 0 : d[1];
      d[1] = 0;
      if ( !( n[0] % 2 ) ) d[n[0]+1] = 0;

      src += n[0];
      dst += n[0] / 2 + 1;

    }

  }

  return E_NONE;

}


static Status RealTransf2
              (Size n[2],
               const Real *src,
               Cmplx *dst,
               Size count,
               void *wk[],
               FourierOpt opt,
               GSLfftData *data)

{
  Status status;

  Size n0inc = n[0] / 2 + 1;

  while ( count-- ) {

    status = RealTransf1( n, src, dst, n[1], wk, 0, data );
    if ( exception( status ) ) return status;

    for ( Size i = 0; i < n0inc;  i++ ) {

      if ( gsl_fft_complex_float_forward( (float *)( dst + i ), n0inc, data[1].n, data[1].wtab, wk[1] ) ) {
        return exception( E_GSLFFT );
      }

    }

    if ( opt & FourierSetZeroorig ) {
      Cset( *dst, 0, 0 );
    }

    if ( opt & FourierDoCenter ) {
      FourierCenterSymCmplx( 2, n, dst, dst );
    }

    src += n[1] * n[0];
    dst += n[1] * n0inc;

  }

  return E_NONE;

}


static Status RealTransf3
              (Size n[3],
               const Real *src,
               Cmplx *dst,
               Size count,
               void *wk[],
               FourierOpt opt,
               GSLfftData *data)

{
  Status status;

  Size n0inc = n[0] / 2 + 1;

  while ( count-- ) {

    status = RealTransf2( n, src, dst, n[2], wk, 0, data );
    if ( exception( status ) ) return status;

    for ( Size i = 0; i < n0inc * n[1];  i++ ) {

      if ( gsl_fft_complex_float_forward( (float *)( dst + i ), n0inc * n[1], data[2].n, data[2].wtab, wk[2] ) ) {
        return exception( E_GSLFFT );
      }

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


extern Status GSLfftRealTransf
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
    case 1:  status = exception( RealTransf1( fou->len, src, dst, count, wk, fou->opt, fou->data ) ); break;
    case 2:  status = exception( RealTransf2( fou->len, src, dst, count, wk, fou->opt, fou->data ) ); break;
    case 3:  status = exception( RealTransf3( fou->len, src, dst, count, wk, fou->opt, fou->data ) ); break;
    default: status = exception( E_FOURIER_DIM );
  }

  return status;

}


static Status ImagTransf1
              (Size n[1],
               const Imag *src,
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
        Cset( *dst, 0, data[0].scale * *(const Real *)src );
        dst++; src++;
      }

    }

  } else {

    while ( count-- ) {

      Real *d = (Real *)dst; d++;
      if ( data[0].scale == 1.0 ) {
        memcpy( d, src, n[0] * sizeof(Real) );
      } else {
        const Real *s = (const Real *)src;
        for ( Size i = 0; i < n[0]; i++ ) {
          d[i] = data[0].scale * s[i];
        }
      }

      if ( gsl_fft_real_float_transform( (float *)d--, 1, data[0].n, data[0].wtab, wk[0] ) ) {
        return exception( E_GSLFFT );
      }
      d[0] = ( opt & FourierSetZeroorig ) ? 0 : d[1];
      d[1] = 0;
      if ( !( n[0] % 2 ) ) d[n[0]+1] = 0;

      FourierMulI( n[0], dst, 1 );

      src += n[0];
      dst += n[0] / 2 + 1;

    }

  }

  return E_NONE;

}


static Status ImagTransf2
              (Size n[2],
               const Imag *src,
               Cmplx *dst,
               Size count,
               void *wk[],
               FourierOpt opt,
               GSLfftData *data)

{
  Status status;

  Size n0inc = n[0] / 2 + 1;

  while ( count-- ) {

    status = RealTransf1( n, (const Real *)src, dst, n[1], wk, 0, data );
    if ( exception( status ) ) return status;

    for ( Size i = 0; i < n0inc;  i++ ) {

      if ( gsl_fft_complex_float_forward( (float *)( dst + i ), n0inc, data[1].n, data[1].wtab, wk[1] ) ) {
        return exception( E_GSLFFT );
      }

      FourierMulI( n[1], dst + i, n0inc );

    }

    if ( opt & FourierSetZeroorig ) {
      Cset( *dst, 0, 0 );
    }

    if ( opt & FourierDoCenter ) {
      FourierCenterSymCmplx( 2, n, dst, dst );
    }

    src += n[1] * n[0];
    dst += n[1] * n0inc;

  }

  return E_NONE;

}


static Status ImagTransf3
              (Size n[3],
               const Imag *src,
               Cmplx *dst,
               Size count,
               void *wk[],
               FourierOpt opt,
               GSLfftData *data)

{
  Status status;

  Size n0inc = n[0] / 2 + 1;

  while ( count-- ) {

    status = RealTransf2( n, (const Real *)src, dst, n[2], wk, 0, data );
    if ( exception( status ) ) return status;

    for ( Size i = 0; i < n0inc * n[1];  i++ ) {

      if ( gsl_fft_complex_float_forward( (float *)( dst + i ), n0inc * n[1], data[2].n, data[2].wtab, wk[2] ) ) {
        return exception( E_GSLFFT );
      }

      FourierMulI( n[2], dst + i, n0inc * n[1] );

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


extern Status GSLfftImagTransf
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
    case 1:  status = exception( ImagTransf1( fou->len, src, dst, count, wk, fou->opt, fou->data ) ); break;
    case 2:  status = exception( ImagTransf2( fou->len, src, dst, count, wk, fou->opt, fou->data ) ); break;
    case 3:  status = exception( ImagTransf3( fou->len, src, dst, count, wk, fou->opt, fou->data ) ); break;
    default: status = exception( E_FOURIER_DIM );
  }

  return status;

}
