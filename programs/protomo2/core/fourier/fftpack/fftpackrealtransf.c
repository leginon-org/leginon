/*----------------------------------------------------------------------------*
*
*  fftpackrealtransf.c  -  fftpack: fast Fourier transforms with fftpack
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "fftpackcommon.h"
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
               float *wk,
               FourierOpt opt,
               FFTpackData *data)

{

  if ( data[0].n != (int)n[0] ) return exception( E_FFTPACK );

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

      rfftf1_( &data[0].n, d--, wk, data[0].wa, data[0].ifac );
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
               float *wk,
               Cmplx *tmp,
               FourierOpt opt,
               FFTpackData *data)

{
  Status status;

  if ( data[0].n != (int)n[0] ) return exception( E_FFTPACK );
  if ( data[1].n != (int)n[1] ) return exception( E_FFTPACK );

  Size n0inc = n[0] / 2 + 1;

  while ( count-- ) {

    status = RealTransf1( n, src, dst, n[1], wk, 0, data );
    if ( exception( status ) ) return status;

    for ( Size i = 0; i < n0inc;  i++ ) {

      FourierPosCmplx2( n[1], dst + i, n0inc, tmp, 1 );

      cfftf1_( &data[1].n, (float *)tmp, wk, data[1].wa, data[1].ifac );

      FourierPosCmplx2( n[1], tmp, 1, dst + i, n0inc );

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
               float *wk,
               Cmplx *tmp,
               FourierOpt opt,
               FFTpackData *data)

{
  Status status;

  if ( data[0].n != (int)n[0] ) return exception( E_FFTPACK );
  if ( data[1].n != (int)n[1] ) return exception( E_FFTPACK );
  if ( data[2].n != (int)n[2] ) return exception( E_FFTPACK );

  Size n0inc = n[0] / 2 + 1;

  while ( count-- ) {

    status = RealTransf2( n, src, dst, n[2], wk, tmp, 0, data );
    if ( exception( status ) ) return status;

    for ( Size i = 0; i < n0inc * n[1];  i++ ) {

      FourierPosCmplx2( n[2], dst + i, n0inc * n[1], tmp, 1 );

      cfftf1_( &data[2].n, (float *)tmp, wk, data[2].wa, data[2].ifac );

      FourierPosCmplx2( n[2], tmp, 1, dst + i, n0inc * n[1] );

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




extern Status FFTpackRealTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count)

{
  FFTpackData *data = fou->data;
  Status status;

  Cmplx *tmp = data->tmp;
  float *wk = (float *)( tmp + data->ntmp );

  switch ( fou->dim ) {
    case 0:  status = exception( E_ARGVAL ); break;
    case 1:  status = exception( RealTransf1( fou->len, src, dst, count, wk, fou->opt, data ) ); break;
    case 2:  status = exception( RealTransf2( fou->len, src, dst, count, wk, tmp, fou->opt, data ) ); break;
    case 3:  status = exception( RealTransf3( fou->len, src, dst, count, wk, tmp, fou->opt, data ) ); break;
    default: status = exception( E_FOURIER_DIM );
  }

  return status;

}



static Status ImagTransf1
              (Size n[1],
               const Imag *src,
               Cmplx *dst,
               Size count,
               float *wk,
               FourierOpt opt,
               FFTpackData *data)

{

  if ( data[0].n != (int)n[0] ) return exception( E_FFTPACK );

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

      rfftf1_( &data[0].n, d--, wk, data[0].wa, data[0].ifac );
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
               float *wk,
               Cmplx *tmp,
               FourierOpt opt,
               FFTpackData *data)

{
  Status status;

  if ( data[0].n != (int)n[0] ) return exception( E_FFTPACK );
  if ( data[1].n != (int)n[1] ) return exception( E_FFTPACK );

  Size n0inc = n[0] / 2 + 1;

  while ( count-- ) {

    status = RealTransf1( n, (const Real *)src, dst, n[1], wk, 0, data );
    if ( exception( status ) ) return status;

    for ( Size i = 0; i < n0inc;  i++ ) {

      FourierPosCmplx2( n[1], dst + i, n0inc, tmp, 1 );

      cfftf1_( &data[1].n, (float *)tmp, wk, data[1].wa, data[1].ifac );

      FourierMulI2( n[1], tmp, 1, dst + i, n0inc );

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
               float *wk,
               Cmplx *tmp,
               FourierOpt opt,
               FFTpackData *data)

{
  Status status;

  if ( data[0].n != (int)n[0] ) return exception( E_FFTPACK );
  if ( data[1].n != (int)n[1] ) return exception( E_FFTPACK );
  if ( data[2].n != (int)n[2] ) return exception( E_FFTPACK );

  Size n0inc = n[0] / 2 + 1;

  while ( count-- ) {

    status = RealTransf2( n, (const Real *)src, dst, n[2], wk, tmp, 0, data );
    if ( exception( status ) ) return status;

    for ( Size i = 0; i < n0inc * n[1];  i++ ) {

      FourierPosCmplx2( n[2], dst + i, n0inc * n[1], tmp, 1 );

      cfftf1_( &data[2].n, (float *)tmp, wk, data[2].wa, data[2].ifac );

      FourierMulI2( n[2], tmp, 1, dst + i, n0inc * n[1] );

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




extern Status FFTpackImagTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count)

{
  FFTpackData *data = fou->data;
  Status status;

  Cmplx *tmp = data->tmp;
  float *wk = (float *)( tmp + data->ntmp );

  switch ( fou->dim ) {
    case 0:  status = exception( E_ARGVAL ); break;
    case 1:  status = exception( ImagTransf1( fou->len, src, dst, count, wk, fou->opt, data ) ); break;
    case 2:  status = exception( ImagTransf2( fou->len, src, dst, count, wk, tmp, fou->opt, data ) ); break;
    case 3:  status = exception( ImagTransf3( fou->len, src, dst, count, wk, tmp, fou->opt, data ) ); break;
    default: status = exception( E_FOURIER_DIM );
  }

  return status;

}


