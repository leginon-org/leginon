/*----------------------------------------------------------------------------*
*
*  djbfftinvcmplxtransf.c  -  djbfft: fast Fourier transforms
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "djbfftcommon.h"
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
               Cmplx *tmp,
               FourierOpt opt,
               DJBfftData *data)

{

  while ( count-- ) {

    if ( opt & FourierDoUncenter ) {
      FourierUncenterAsymCmplx( 1, n, src, tmp );
    } else {
      memcpy( tmp, src, n[0] * sizeof(Cmplx) );
    }

    if ( opt & FourierSetZeromean ) {
      Cset( *tmp, 0, 0 );
    }

    if ( data[0].scale == 1.0 ) {
      for ( Size i = 0; i < n[0]; i++ ) {
        dst[i] = tmp[ data[0].ctab[i] ];
      }
    } else {
      for ( Size i = 0; i < n[0]; i++ ) {
        Cmplx p = tmp[ data[0].ctab[i] ];
        Cset( dst[i], data[0].scale * Re( p ), data[0].scale * Im( p ) );
      }
    }

    data[0].bc( dst );

    src += n[0];
    dst += n[0];

  }

  return E_NONE;

}


static Status InvCmplxTransf2
              (Size n[2],
               const Cmplx *src,
               Cmplx *dst,
               Size count,
               Cmplx *tmp,
               FourierOpt opt,
               DJBfftData *data)

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

      DJBbackPosCmplx2( n[1], dst + i, n[0], tmp, data[1].ctab );

      data[1].bc( tmp );

      FourierPosCmplx2( n[1], tmp, 1, dst + i, n[0] );

    }

    status = InvCmplxTransf1( n, dst, dst, n[1], tmp, 0, data );
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
               Cmplx *tmp,
               FourierOpt opt,
               DJBfftData *data)

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

      DJBbackPosCmplx2( n[2], dst + i, n[0] * n[1], tmp, data[2].ctab );

      data[2].bc( tmp );

      FourierPosCmplx2( n[2], tmp, 1, dst + i, n[0] * n[1] );

    }

    status = InvCmplxTransf2( n, dst, dst, n[2], tmp, 0, data );
    if ( exception( status ) ) return status;

    src += n[0] * n[1] * n[2];
    dst += n[0] * n[1] * n[2];

  }

  return E_NONE;

}




extern Status DJBfftInvCmplxTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count)

{
  DJBfftData *data = fou->data;
  void *tmp = data[0].tmp;
  Status status;

  if ( fou->opt & FourierDoCenter ) {
    return exception( E_DJBFFT_OPT );
  }

  switch ( fou->dim ) {
    case 0:  status = exception( E_ARGVAL ); break;
    case 1:  status = exception( InvCmplxTransf1( fou->len, src, dst, count, tmp, fou->opt, data ) ); break;
    case 2:  status = exception( InvCmplxTransf2( fou->len, src, dst, count, tmp, fou->opt, data ) ); break;
    case 3:  status = exception( InvCmplxTransf3( fou->len, src, dst, count, tmp, fou->opt, data ) ); break;
    default: status = exception( E_FOURIER_DIM );
  }

  return status;

}


