/*----------------------------------------------------------------------------*
*
*  fftw2invrealtransf.c  -  fftw2: fast Fourier transforms with fftw version 2
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
#include <string.h>


/* functions */

static Status InvRealTransf1
              (Size n[1],
               const Cmplx *src,
               Real *dst,
               Size count,
               FourierOpt opt,
               FFTW2data *data)

{
  if ( n[0] == 1 ) {

    if ( opt & FourierSetZeromean ) {

      while ( count-- ) {
        *dst++ = 0;
      }

    } else {

      while ( count-- ) {
        *dst++ = data[0].scale * Re( *src++ );
      }

    }

    return E_NONE;

  }

  rfftw_plan plan = data->plan;

  if ( plan == NULL ) {

    int flags = data->flags | FFTW_OUT_OF_PLACE;
    if ( !FFTW2_BEGIN_CRITICAL ) {
      if ( data->plan == NULL ) {
        plan = data->plan = rfftw_create_plan( n[0], FFTW_BACKWARD, flags );
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

    if ( data->scale == 1.0 ) {

      tmp[0] = ( opt & FourierSetZeromean ) ? 0 : Re( *src++ );

      for ( Size i = 1; i < ( n[0] + 1 ) / 2; i++ ) {
        tmp[i] = Re( *src );
        tmp[n[0]-i] = Im( *src );
        src++;
      }

      if ( n[0] % 2 == 0 ) {
        tmp[n[0]/2] = Re( *src++ );
      }

    } else {

      tmp[0] = ( opt & FourierSetZeromean ) ? 0 : data->scale * Re( *src++ );

      for ( Size i = 1; i < ( n[0] + 1 ) / 2; i++ ) {
        tmp[i] = data->scale * Re( *src );
        tmp[n[0]-i] = data->scale * Im( *src );
        src++;
      }

      if ( n[0] % 2 == 0 ) {
        tmp[n[0]/2] = data->scale * Re( *src++ );
      }

    }

    FFTW2_rr_1( plan, tmp, dst );

    dst += n[0];

  }

#ifdef FFTW2_THREADS
  free( tmp );
#endif

  return E_NONE;

}


static Status InvRealTransf2
              (Size n[2],
               const Cmplx *src,
               Real *dst,
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
        plan = data->plan = rfftw2d_create_plan( n[1], n[0], FFTW_BACKWARD, flags );
      } else {
        plan = data->plan;
      }
      if ( FFTW2_END_CRITICAL || ( plan == NULL ) ) {
        return exception( E_FFTW2_INIT );
      }
    }
    data->type = FFTW2_PLAN_rfftwnd;

  }

  Cmplx *tmp = data->tmp;

  if ( tmp == NULL ) {

    tmp = malloc( n02 * n[1] * sizeof(Cmplx) );
    if ( tmp == NULL ) {
      return exception( E_MALLOC );
    }
#ifndef FFTW2_THREADS
    data->tmp = tmp;
#endif

  }

  while ( count-- ) {

    if ( opt & FourierDoUncenter ) {
      FourierUncenterSymCmplx( 2, n, src, tmp );
    } else {
      memcpy( tmp, src, n02 * n[1] * sizeof(Cmplx) );
    }

    if ( data->scale != 1.0 ) {
      for ( Size i = 0; i < n02 * n[1]; i++ ) {
        Cset( tmp[i], data->scale * Re( tmp[i] ), data->scale * Im( tmp[i] ) );
      }
    }

    if ( opt & FourierSetZeromean ) {
      Cset( *tmp, 0, 0 );
    }

    FFTW2_cr_n( plan, tmp, dst );

    src += n02 * n[1];
    dst += n[0] * n[1];

  }

#ifdef FFTW2_THREADS
  free( tmp );
#endif

  return E_NONE;

}


static Status InvRealTransf3
              (Size n[3],
               const Cmplx *src,
               Real *dst,
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
        plan = data->plan = rfftw3d_create_plan( n[2], n[1], n[0], FFTW_BACKWARD, flags );
      } else {
        plan = data->plan;
      }
      if ( FFTW2_END_CRITICAL || ( plan == NULL ) ) {
        return exception( E_FFTW2_INIT );
      }
    }
    data->type = FFTW2_PLAN_rfftwnd;

  }

  Cmplx *tmp = data->tmp;

  if ( tmp == NULL ) {

    tmp = malloc( n02 * n[1] * n[2] * sizeof(Cmplx) );
    if ( tmp == NULL ) {
      return exception( E_MALLOC );
    }
#ifndef FFTW2_THREADS
    data->tmp = tmp;
#endif

  }

  while ( count-- ) {

    if ( opt & FourierDoUncenter ) {
      FourierUncenterSymCmplx( 3, n, src, tmp );
    } else {
      memcpy( tmp, src, n02 * n[1] * n[2] * sizeof(Cmplx) );
    }

    if ( data->scale != 1.0 ) {
      for ( Size i = 0; i < n02 * n[1] * n[2]; i++ ) {
        Cset( tmp[i], data->scale * Re( tmp[i] ), data->scale * Im( tmp[i] ) );
      }
    }

    if ( opt & FourierSetZeromean ) {
      Cset( *tmp, 0, 0 );
    }

    FFTW2_cr_n( plan, tmp, dst );

    src += n02 * n[1] * n[2];
    dst += n[0] * n[1] * n[2];

  }

#ifdef FFTW2_THREADS
  free( tmp );
#endif

  return E_NONE;

}




extern Status FFTW2InvRealTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count)

{
  Status status;

  if ( fou->opt & FourierDoCenter ) {
    return exception( E_FFTW2_OPT );
  }

  switch ( fou->dim ) {
    case 0:  return exception( E_ARGVAL );
    case 1:  status = exception( InvRealTransf1( fou->len, src, dst, count, fou->opt, fou->data ) ); break;
    case 2:  status = exception( InvRealTransf2( fou->len, src, dst, count, fou->opt, fou->data ) ); break;
    case 3:  status = exception( InvRealTransf3( fou->len, src, dst, count, fou->opt, fou->data ) ); break;
    default: return exception( E_FOURIER_DIM );
  }

  return status;

}


