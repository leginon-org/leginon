/*----------------------------------------------------------------------------*
*
*  fftpackinvcmplxtransf.c  -  fftpack: fast Fourier transforms with fftpack
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

static Status InvCmplxTransf1
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

    if ( opt & FourierSetZeromean ) {

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

  } else if ( opt & FourierDoUncenter ) {

    while ( count-- ) {

      FourierUncenterAsymCmplx( 1, n, src, dst );

      if ( opt & FourierSetZeromean ) {
        Cset( *dst, 0, 0 );
      }

      cfftb1_( &data[0].n, (float *)dst, wk, data[0].wa, data[0].ifac );

      if ( data[0].scale != 1.0 ) {
        Cmplx *d = dst, *de = d + n[0];
        while ( d < de ) {
          Cset( *d, data[0].scale * Re( *d ), data[0].scale * Im( *d ) ); d++;
        }
      }

      src += n[0];
      dst += n[0];

    }

  } else {

    while ( count-- ) {

      if ( src != dst ) {
        memcpy( dst, src, n[0] * sizeof(Cmplx) );
      }

      if ( opt & FourierSetZeromean ) {
        Cset( *dst, 0, 0 );
      }

      cfftb1_( &data[0].n, (float *)dst, wk, data[0].wa, data[0].ifac );

      if ( data[0].scale != 1.0 ) {
        Cmplx *d = dst, *de = d + n[0];
        while ( d < de ) {
          Cset( *d, data[0].scale * Re( *d ), data[0].scale * Im( *d ) ); d++;
        }
      }

      src += n[0];
      dst += n[0];

    }

  }

  return E_NONE;

}


static Status InvCmplxTransf2
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

    if ( opt & FourierDoUncenter ) {
      FourierUncenterAsymCmplx( 2, n, src, dst );
    } else {
      memcpy( dst, src, n[0] * n[1] * sizeof(Cmplx) );
    }

    if ( opt & FourierSetZeromean ) {
      Cset( *dst, 0, 0 );
    }

    for ( Size i = 0; i < n[0];  i++ ) {

      FourierPosCmplx2( n[1], dst + i, n[0], tmp, 1 );

      cfftb1_( &data[1].n, (float *)tmp, wk, data[1].wa, data[1].ifac );

      FourierPosCmplx2( n[1], tmp, 1, dst + i, n[0] );

    }

    status = InvCmplxTransf1( n, dst, dst, n[1], wk, 0, data );
    if ( exception( status ) ) return status;

    src += n[0] * n[1];
    dst += n[0] * n[1];

  }

  return E_NONE;

}


static Status InvCmplxTransf3
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

    if ( opt & FourierDoUncenter ) {
      FourierUncenterAsymCmplx( 3, n, src, dst );
    } else {
      memcpy( dst, src, n[0] * n[1] * n[2] * sizeof(Cmplx) );
    }

    if ( opt & FourierSetZeromean ) {
      Cset( *dst, 0, 0 );
    }

    for ( Size i = 0; i < n[0] * n[1];  i++ ) {

      FourierPosCmplx2( n[2], dst + i, n[0] * n[1], tmp, 1 );

      cfftb1_( &data[2].n, (float *)tmp, wk, data[2].wa, data[2].ifac );

      FourierPosCmplx2( n[2], tmp, 1, dst + i, n[0] * n[1] );

    }

    status = InvCmplxTransf2( n, dst, dst, n[2], wk, tmp, 0, data );
    if ( exception( status ) ) return status;

    src += n[0] * n[1] * n[2];
    dst += n[0] * n[1] * n[2];

  }

  return E_NONE;

}




extern Status FFTpackInvCmplxTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count)

{
  FFTpackData *data = fou->data;
  Status status;

  if ( fou->opt & FourierDoCenter ) {
    return exception( E_FFTPACK_OPT );
  }

  Cmplx *tmp = data->tmp;
  float *wk = (float *)( tmp + data->ntmp );

  switch ( fou->dim ) {
    case 0:  status = exception( E_ARGVAL ); break;
    case 1:  status = exception( InvCmplxTransf1( fou->len, src, dst, count, wk, fou->opt, data ) ); break;
    case 2:  status = exception( InvCmplxTransf2( fou->len, src, dst, count, wk, tmp, fou->opt, data ) ); break;
    case 3:  status = exception( InvCmplxTransf3( fou->len, src, dst, count, wk, tmp, fou->opt, data ) ); break;
    default: status = exception( E_FOURIER_DIM );
  }

  return status;

}


