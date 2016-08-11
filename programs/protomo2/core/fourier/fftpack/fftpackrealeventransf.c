/*----------------------------------------------------------------------------*
*
*  fftpackrealeventransf.c  -  fftpack: fast Fourier transforms with fftpack
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


/* functions */

static Status RealEvenTransf1
              (Size n[1],
               const Real *src,
               Real *dst,
               Size count,
               float *wk,
               Cmplx *tmp,
               FourierOpt opt,
               FFTpackData *data)

{

  if ( data[0].n != (int)n[0] ) return exception( E_FFTPACK );

  if ( n[0] == 1 ) {

    if ( opt & FourierSetZeroorig ) {

      while ( count-- ) {
        *dst++ = 0;
      }

    } else {

      while ( count-- ) {
        *dst++ = data[0].scale * *src++;
      }

    }

  } else {

    Size n0inc = n[0] / 2 + 1;

    while ( count-- ) {

      Real *rtmp = (Real *)tmp;
      if ( data[0].scale == 1.0 ) {
        FourierExtRealEven2( n[0], src, 1, rtmp, 1 );
      } else {
        for ( Size i = 0; i < n0inc; i++ ) {
          rtmp[i] = data[0].scale * src[i];
        }
        FourierExtRealEven( n[0], rtmp, 1 );
      }

      rfftf1_( &data[0].n, rtmp, wk, data[0].wa, data[0].ifac );

      dst[0] = ( opt & FourierSetZeroorig ) ? 0 : *rtmp++;
      for ( Size i = 1; i < n0inc; i++ ) {
        dst[i] = *rtmp; rtmp += 2;
      }

      src += n0inc;
      dst += n0inc;

    }

  }

  return E_NONE;

}




extern Status FFTpackRealEvenTransf
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
    case 1:  status = exception( RealEvenTransf1( fou->len, src, dst, count, wk, tmp, fou->opt, data ) ); break;
    default: status = exception( E_FOURIER_DIM );
  }

  return status;

}


