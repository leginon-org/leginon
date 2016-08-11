/*----------------------------------------------------------------------------*
*
*  fftw2cmplxtransf.c  -  fftw2: fast Fourier transforms with fftw version 2
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

static Status CmplxTransf1
              (Size n[1],
               const Cmplx *src,
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
        Cset( *dst, data[0].scale * Re( *src ), Im( *src ) );
        dst++; src++;
      }

    }

    return E_NONE;

  }

  fftw_plan plan = data->plan;

  if ( plan == NULL ) {

    int flags = data->flags | FFTW_OUT_OF_PLACE;
    if ( !FFTW2_BEGIN_CRITICAL ) {
      if ( data->plan == NULL ) {
        plan = data->plan = fftw_create_plan( n[0], FFTW_FORWARD, flags );
      } else {
        plan = data->plan;
      }
      if ( FFTW2_END_CRITICAL || ( plan == NULL ) ) {
        return exception( E_FFTW2_INIT );
      }
    }
    data->type = FFTW2_PLAN_fftw;

  }

  while ( count-- ) {

    FFTW2_c_1( plan, src, dst );

    if ( data->scale != 1.0 ) {
      for ( Size i = 0; i < n[0]; i++ ) {
        Cset( dst[i], data->scale * Re( dst[i] ), data->scale * Im( dst[i] ) );
      }
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

  return E_NONE;

}


static Status CmplxTransf2
              (Size n[2],
               const Cmplx *src,
               Cmplx *dst,
               Size count,
               FourierOpt opt,
               FFTW2data *data)

{
  fftwnd_plan plan = data->plan;

  if ( plan == NULL ) {

    int flags = data->flags | FFTW_OUT_OF_PLACE;
    if ( !FFTW2_BEGIN_CRITICAL ) {
      if ( data->plan == NULL ) {
        plan = data->plan = fftw2d_create_plan( n[1], n[0], FFTW_FORWARD, flags );
      } else {
        plan = data->plan;
      }
      if ( FFTW2_END_CRITICAL || ( plan == NULL ) ) {
        return exception( E_FFTW2_INIT );
      }
    }
    data->type = FFTW2_PLAN_fftwnd;

  }

  while ( count-- ) {

    FFTW2_c_n( plan, src, dst );

    if ( data->scale != 1.0 ) {
      for ( Size i = 0; i < n[0] * n[1]; i++ ) {
        Cset( dst[i], data->scale * Re( dst[i] ), data->scale * Im( dst[i] ) );
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
               FourierOpt opt,
               FFTW2data *data)

{
  fftwnd_plan plan = data->plan;

  if ( plan == NULL ) {

    int flags = data->flags | FFTW_OUT_OF_PLACE;
    if ( !FFTW2_BEGIN_CRITICAL ) {
      if ( data->plan == NULL ) {
        plan = data->plan = fftw3d_create_plan( n[2], n[1], n[0], FFTW_FORWARD, flags );
      } else {
        plan = data->plan;
      }
      if ( FFTW2_END_CRITICAL || ( plan == NULL ) ) {
        return exception( E_FFTW2_INIT );
      }
    }
    data->type = FFTW2_PLAN_fftwnd;

  }

  while ( count-- ) {

    FFTW2_c_n( plan, src, dst );

    if ( data->scale != 1.0 ) {
      for ( Size i = 0; i < n[0] * n[1] * n[2]; i++ ) {
        Cset( dst[i], data->scale * Re( dst[i] ), data->scale * Im( dst[i] ) );
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




extern Status FFTW2CmplxTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count)

{
  Status status;

  switch ( fou->dim ) {
    case 0:  return exception( E_ARGVAL );
    case 1:  status = exception( CmplxTransf1( fou->len, src, dst, count, fou->opt, fou->data ) ); break;
    case 2:  status = exception( CmplxTransf2( fou->len, src, dst, count, fou->opt, fou->data ) ); break;
    case 3:  status = exception( CmplxTransf3( fou->len, src, dst, count, fou->opt, fou->data ) ); break;
    default: return exception( E_FOURIER_DIM );
  }

  return status;

}


