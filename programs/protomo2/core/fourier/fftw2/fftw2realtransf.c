/*----------------------------------------------------------------------------*
*
*  fftw2realtransf.c  -  fftw2: fast Fourier transforms with fftw version 2
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "fftw2common.h"
#include "exception.h"
#include "mathdefs.h"
#include <stdlib.h>


/* functions */

static Status RealTransf1
              (Size n[1],
               const Real *src,
               Cmplx *dst,
               Size count,
               FourierOpt opt,
               FFTW2data *data)

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

    return E_NONE;

  }

  rfftw_plan plan = data->plan;

  if ( plan == NULL ) {

    int flags = data->flags | FFTW_OUT_OF_PLACE;
    if ( !FFTW2_BEGIN_CRITICAL ) {
      if ( data->plan == NULL ) {
        plan = data->plan = rfftw_create_plan( n[0], FFTW_FORWARD, flags );
      } else {
        plan = data->plan;
      }
      if ( FFTW2_END_CRITICAL || ( plan == NULL ) ) {
        return exception( E_FFTW2_INIT );
      }
    }
    data->type = FFTW2_PLAN_rfftw;

  }

  Real *tmp = data->tmp;

  if ( tmp == NULL ) {

    tmp = malloc( n[0] * sizeof(Real) );
    if ( tmp == NULL ) {
      return exception( E_MALLOC );
    }
#ifndef FFTW2_THREADS
    data->tmp = tmp;
#endif

  }

  while ( count-- ) {

    FFTW2_rr_1( plan, src, tmp );

    if ( data->scale == 1.0 ) {

      Cset( dst[0], ( opt & FourierSetZeroorig ) ? 0 : tmp[0], 0 );

      for ( Size i = 1; i < ( n[0] + 1 ) / 2; i++ ) {
        Cset( dst[i], tmp[i], tmp[ n[0] - i ] );
      }

      if ( n[0] % 2 == 0 ) {
        Cset( dst[ n[0] / 2 ], tmp[ n[0] / 2 ], 0 );
      }

    } else {

      Cset( dst[0], ( opt & FourierSetZeroorig ) ? 0 : data->scale * tmp[0], 0 );

      for ( Size i = 1; i < ( n[0] + 1 ) / 2; i++ ) {
        Cset( dst[i], data->scale * tmp[i], data->scale * tmp[ n[0] - i ] );
      }

      if ( n[0] % 2 == 0 ) {
        Cset( dst[ n[0] / 2 ], data->scale * tmp[ n[0] / 2 ], 0 );
      }

    }

    src += n[0];
    dst += n[0] / 2 + 1;

  }

#ifdef FFTW2_THREADS
  free( tmp );
#endif

  return E_NONE;

}


static Status RealTransf2
              (Size n[2],
               const Real *src,
               Cmplx *dst,
               Size count,
               FourierOpt opt,
               FFTW2data *data)

{
  Size n02 = n[0] / 2 + 1;
  rfftwnd_plan plan = data->plan;

  if ( plan == NULL ) {

    int flags = data->flags | FFTW_OUT_OF_PLACE;
    if ( !FFTW2_BEGIN_CRITICAL ) {
      if ( data->plan == NULL ) {
        plan = data->plan = rfftw2d_create_plan( n[1], n[0], FFTW_FORWARD, flags );
      } else {
        plan = data->plan;
      }
      if ( FFTW2_END_CRITICAL || ( plan == NULL ) ) {
        return exception( E_FFTW2_INIT );
      }
    }
    data->type = FFTW2_PLAN_rfftwnd;

  }

  while ( count-- ) {

    FFTW2_rc_n( plan, src, dst );

    if ( data->scale != 1.0 ) {
      for ( Size i = 0; i < n02 * n[1]; i++ ) {
        Cset( dst[i], data->scale * Re( dst[i] ), data->scale * Im( dst[i] ) );
      }
    }

    if ( opt & FourierSetZeroorig ) {
      Cset( *dst, 0, 0 );
    }

    if ( opt & FourierDoCenter ) {
      FourierCenterSymCmplx( 2, n, dst, dst );
    }

    src += n[0] * n[1];
    dst += n02 * n[1];

  }

  return E_NONE;

}


static Status RealTransf3
              (Size n[3],
               const Real *src,
               Cmplx *dst,
               Size count,
               FourierOpt opt,
               FFTW2data *data)

{
  Size n02 = n[0] / 2 + 1;
  rfftwnd_plan plan = data->plan;

  if ( plan == NULL ) {

    int flags = data->flags | FFTW_OUT_OF_PLACE;
    if ( !FFTW2_BEGIN_CRITICAL ) {
      if ( data->plan == NULL ) {
        plan = data->plan = rfftw3d_create_plan( n[2], n[1], n[0], FFTW_FORWARD, flags );
      } else {
        plan = data->plan;
      }
      if ( FFTW2_END_CRITICAL || ( plan == NULL ) ) {
        return exception( E_FFTW2_INIT );
      }
    }
    data->type = FFTW2_PLAN_rfftwnd;

  }

  while ( count-- ) {

    FFTW2_rc_n( plan, src, dst );

    if ( data->scale != 1.0 ) {
      for ( Size i = 0; i < n02 * n[1] * n[2]; i++ ) {
        Cset( dst[i], data->scale * Re( dst[i] ), data->scale * Im( dst[i] ) );
      }
    }

    if ( opt & FourierSetZeroorig ) {
      Cset( *dst, 0, 0 );
    }

    if ( opt & FourierDoCenter ) {
      FourierCenterSymCmplx( 3, n, dst, dst );
    }

    src += n[0] * n[1] * n[2];
    dst += n02 * n[1] * n[2];

  }

  return E_NONE;

}




extern Status FFTW2RealTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count)

{
  Status status;

  switch ( fou->dim ) {
    case 0:  return exception( E_ARGVAL );
    case 1:  status = exception( RealTransf1( fou->len, src, dst, count, fou->opt, fou->data ) ); break;
    case 2:  status = exception( RealTransf2( fou->len, src, dst, count, fou->opt, fou->data ) ); break;
    case 3:  status = exception( RealTransf3( fou->len, src, dst, count, fou->opt, fou->data ) ); break;
    default: return exception( E_FOURIER_DIM );
  }

  return status;

}


