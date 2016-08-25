/*----------------------------------------------------------------------------*
*
*  fftpackcmplxtransf.c  -  fftpack: fast Fourier transforms with fftpack
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

static Status CmplxTransf1
              (Size n[1],
               const Cmplx *src,
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

      cfftf1_( &data[0].n, (float *)dst, wk, data[0].wa, data[0].ifac );

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
               float *wk,
               Cmplx *tmp,
               FourierOpt opt,
               FFTpackData *data)

{
  Status status;

  if ( data[0].n != (int)n[0] ) return exception( E_FFTPACK );
  if ( data[1].n != (int)n[1] ) return exception( E_FFTPACK );

  while ( count-- ) {

    status = CmplxTransf1( n, src, dst, n[1], wk, 0, data );
    if ( exception( status ) ) return status;

    for ( Size i = 0; i < n[0];  i++ ) {

      FourierPosCmplx2( n[1], dst + i, n[0], tmp, 1 );

      cfftf1_( &data[1].n, (float *)tmp, wk, data[1].wa, data[1].ifac );

      FourierPosCmplx2( n[1], tmp, 1, dst + i, n[0] );

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
               float *wk,
               Cmplx *tmp,
               FourierOpt opt,
               FFTpackData *data)

{
  Status status;

  if ( data[0].n != (int)n[0] ) return exception( E_FFTPACK );
  if ( data[1].n != (int)n[1] ) return exception( E_FFTPACK );
  if ( data[2].n != (int)n[2] ) return exception( E_FFTPACK );

  while ( count-- ) {

    status = CmplxTransf2( n, src, dst, n[2], wk, tmp, 0, data );
    if ( exception( status ) ) return status;

    for ( Size i = 0; i < n[0] * n[1];  i++ ) {

      FourierPosCmplx2( n[2], dst + i, n[0] * n[1], tmp, 1 );

      cfftf1_( &data[2].n, (float *)tmp, wk, data[2].wa, data[2].ifac );

      FourierPosCmplx2( n[2], tmp, 1, dst + i, n[0] * n[1] );

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




extern Status FFTpackCmplxTransf
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
    case 1:  status = exception( CmplxTransf1( fou->len, src, dst, count, wk, fou->opt, data ) ); break;
    case 2:  status = exception( CmplxTransf2( fou->len, src, dst, count, wk, tmp, fou->opt, data ) ); break;
    case 3:  status = exception( CmplxTransf3( fou->len, src, dst, count, wk, tmp, fou->opt, data ) ); break;
    default: status = exception( E_FOURIER_DIM );
  }

  return status;

}


