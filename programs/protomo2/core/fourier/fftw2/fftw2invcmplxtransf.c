/*----------------------------------------------------------------------------*
*
*  fftw2invcmplxtransf.c  -  fftw2: fast Fourier transforms with fftw version 2
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

static Status InvCmplxTransf1
              (Size n[1],
               const Cmplx *src,
               Cmplx *dst,
               Size count,
               FourierOpt opt,
               FFTW2data *data)

{

  if ( n[0] == 1 ) {

    if ( opt & FourierSetZeromean ) {

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
        plan = data->plan = fftw_create_plan( n[0], FFTW_BACKWARD, flags );
      } else {
        plan = data->plan;
      }
      if ( FFTW2_END_CRITICAL || ( plan == NULL ) ) {
        return exception( E_FFTW2_INIT );
      }
    }
    data->type = FFTW2_PLAN_fftw;

  }

  Cmplx *tmp = data->tmp;

  if ( ( tmp == NULL ) && ( ( opt & ( FourierDoUncenter | FourierSetZeromean ) ) || ( data->scale != 1.0 ) ) ) {

    tmp = malloc( n[0] * sizeof(Cmplx) );
    if ( tmp == NULL ) {
      return exception( E_MALLOC );
    }
#ifndef FFTW2_THREADS
    data->tmp = tmp;
#endif

  }

  const Cmplx *ptr = tmp;

  while ( count-- ) {

    if ( opt & FourierDoUncenter ) {
      FourierUncenterAsymCmplx( 1, n, src, tmp );
      if ( data->scale != 1.0 ) {
        for ( Size i = 0; i < n[0]; i++ ) {
          Cset( tmp[i], data->scale * Re( tmp[i] ), data->scale * Im( tmp[i] ) );
        }
      }
    } else if ( opt & FourierSetZeromean || ( data->scale != 1.0 ) ) {
      if ( data->scale != 1.0 ) {
        for ( Size i = 0; i < n[0]; i++ ) {
          Cset( tmp[i], data->scale * Re( src[i] ), data->scale * Im( src[i] ) );
        }
      } else {
        memcpy( tmp, src, n[0] * sizeof(Cmplx) );
      }
    } else {
      ptr = src;
    }

    if ( opt & FourierSetZeromean ) {
      Cset( *tmp, 0, 0 );
    }

    FFTW2_c_1( plan, ptr, dst );

    src += n[0];
    dst += n[0];

  }

#ifdef FFTW2_THREADS
  if ( tmp != NULL ) free( tmp );
#endif

  return E_NONE;

}


static Status InvCmplxTransf2
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
        plan = data->plan = fftw2d_create_plan( n[1], n[0], FFTW_BACKWARD, flags );
      } else {
        plan = data->plan;
      }
      if ( FFTW2_END_CRITICAL || ( plan == NULL ) ) {
        return exception( E_FFTW2_INIT );
      }
    }
    data->type = FFTW2_PLAN_fftwnd;

  }

  Cmplx *tmp = data->tmp;

  if ( ( tmp == NULL ) && ( ( opt & ( FourierDoUncenter | FourierSetZeromean ) ) || ( data->scale != 1.0 ) ) ) {

    tmp = malloc( n[0] * n[1] * sizeof(Cmplx) );
    if ( tmp == NULL ) {
      return exception( E_MALLOC );
    }
#ifndef FFTW2_THREADS
    data->tmp = tmp;
#endif

  }

  const Cmplx *ptr = tmp;

  while ( count-- ) {

    if ( opt & FourierDoUncenter ) {
      FourierUncenterAsymCmplx( 2, n, src, tmp );
      if ( data->scale != 1.0 ) {
        for ( Size i = 0; i < n[0] * n[1]; i++ ) {
          Cset( tmp[i], data->scale * Re( tmp[i] ), data->scale * Im( tmp[i] ) );
        }
      }
    } else if ( opt & FourierSetZeromean || ( data->scale != 1.0 ) )  {
      if ( data->scale != 1.0 ) {
        for ( Size i = 0; i < n[0] * n[1]; i++ ) {
          Cset( tmp[i], data->scale * Re( src[i] ), data->scale * Im( src[i] ) );
        }
      } else {
        memcpy( tmp, src, n[0] * n[1] * sizeof(Cmplx) );
      }
    } else {
      ptr = src;
    }

    if ( opt & FourierSetZeromean ) {
      Cset( *tmp, 0, 0 );
    }

    FFTW2_c_n( plan, ptr, dst );

    src += n[0] * n[1];
    dst += n[0] * n[1];

  }

#ifdef FFTW2_THREADS
  if ( tmp != NULL ) free( tmp );
#endif

  return E_NONE;

}


static Status InvCmplxTransf3
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
        plan = data->plan = fftw3d_create_plan( n[2], n[1], n[0], FFTW_BACKWARD, flags );
      } else {
        plan = data->plan;
      }
      if ( FFTW2_END_CRITICAL || ( plan == NULL ) ) {
        return exception( E_FFTW2_INIT );
      }
    }
    data->type = FFTW2_PLAN_fftwnd;

  }

  Cmplx *tmp = data->tmp;

  if ( ( tmp == NULL ) && ( ( opt & ( FourierDoUncenter | FourierSetZeromean ) ) || ( data->scale != 1.0 ) ) ) {

    tmp = malloc( n[0] * n[1] * n[2] * sizeof(Cmplx) );
    if ( tmp == NULL ) {
      return exception( E_MALLOC );
    }
#ifndef FFTW2_THREADS
    data->tmp = tmp;
#endif

  }

  const Cmplx *ptr = tmp;

  while ( count-- ) {

    if ( opt & FourierDoUncenter ) {
      FourierUncenterAsymCmplx( 3, n, src, tmp );
      if ( data->scale != 1.0 ) {
        for ( Size i = 0; i < n[0] * n[1] * n[2]; i++ ) {
          Cset( tmp[i], data->scale * Re( tmp[i] ), data->scale * Im( tmp[i] ) );
        }
      }
    } else if ( opt & FourierSetZeromean || ( data->scale != 1.0 ) )  {
      if ( data->scale != 1.0 ) {
        for ( Size i = 0; i < n[0] * n[1] * n[2]; i++ ) {
          Cset( tmp[i], data->scale * Re( src[i] ), data->scale * Im( src[i] ) );
        }
      } else {
        memcpy( tmp, src, n[0] * n[1] * n[2] * sizeof(Cmplx) );
      }
    } else {
      ptr = src;
    }

    if ( opt & FourierSetZeromean ) {
      Cset( *tmp, 0, 0 );
    }

    FFTW2_c_n( plan, ptr, dst );

    src += n[0] * n[1] * n[2];
    dst += n[0] * n[1] * n[2];

  }

#ifdef FFTW2_THREADS
  if ( tmp != NULL ) free( tmp );
#endif

  return E_NONE;

}




extern Status FFTW2InvCmplxTransf
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
    case 1:  status = exception( InvCmplxTransf1( fou->len, src, dst, count, fou->opt, fou->data ) ); break;
    case 2:  status = exception( InvCmplxTransf2( fou->len, src, dst, count, fou->opt, fou->data ) ); break;
    case 3:  status = exception( InvCmplxTransf3( fou->len, src, dst, count, fou->opt, fou->data ) ); break;
    default: return exception( E_FOURIER_DIM );
  }

  return status;

}


