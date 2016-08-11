/*----------------------------------------------------------------------------*
*
*  gslfftinvcmplxtransf.c  -  gslfft: fast Fourier transforms with gsl
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

static Status InvCmplxTransf1
              (Size n[1],
               const Cmplx *src,
               Cmplx *dst,
               Size count,
               void *wk[],
               FourierOpt opt,
               GSLfftData *data)

{

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

      if ( gsl_fft_complex_float_backward( (float *)dst, 1, data[0].n, data[0].wtab, wk[0] ) ) {
        return exception( E_GSLFFT );
      }

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

      if ( gsl_fft_complex_float_backward( (float *)dst, 1, data[0].n, data[0].wtab, wk[0] ) ) {
        return exception( E_GSLFFT );
      }

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
               void *wk[],
               FourierOpt opt,
               GSLfftData *data)

{
  Status status;

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

      if ( gsl_fft_complex_float_backward( (float *)( dst + i ), n[0], data[1].n, data[1].wtab, wk[1] ) ) {
        return exception( E_GSLFFT );
      }

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
               void *wk[],
               FourierOpt opt,
               GSLfftData *data)

{
  Status status;

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

      if ( gsl_fft_complex_float_backward( (float *)( dst + i ), n[0] * n[1], data[2].n, data[2].wtab, wk[2] ) ) {
        return exception( E_GSLFFT );
      }

    }

    status = InvCmplxTransf2( n, dst, dst, n[2], wk, 0, data );
    if ( exception( status ) ) return status;

    src += n[0] * n[1] * n[2];
    dst += n[0] * n[1] * n[2];

  }

  return E_NONE;

}


extern Status GSLfftInvCmplxTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count)

{
  void *wk[3];
  Status status;

  if ( fou->opt & FourierDoCenter ) {
    return exception( E_GSLFFT_OPT );
  }

  status = GSLfftWk( fou->dim, fou->data, wk, sizeof(wk) );
  if ( exception( status ) ) return status;

  switch ( fou->dim ) {
    case 0:  status = exception( E_ARGVAL ); break;
    case 1:  status = exception( InvCmplxTransf1( fou->len, src, dst, count, wk, fou->opt, fou->data ) ); break;
    case 2:  status = exception( InvCmplxTransf2( fou->len, src, dst, count, wk, fou->opt, fou->data ) ); break;
    case 3:  status = exception( InvCmplxTransf3( fou->len, src, dst, count, wk, fou->opt, fou->data ) ); break;
    default: status = exception( E_FOURIER_DIM );
  }

  return status;

}
