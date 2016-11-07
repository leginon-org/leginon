/*----------------------------------------------------------------------------*
*
*  djbfftcmplxtransf.c  -  djbfft: fast Fourier transforms
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

static Status CmplxTransf1
              (Size n[1],
               const Cmplx *src,
               Cmplx *dst,
               Size count,
               Cmplx *tmp,
               FourierOpt opt,
               DJBfftData *data)

{

  while ( count-- ) {

    memcpy( tmp, src, n[0] * sizeof(Cmplx) );

    data[0].fc( tmp );

    if ( data[0].scale == 1.0 ) {
      for ( Size i = 0; i < n[0]; i++ ) {
        dst[ data[0].ctab[i] ] = tmp[i];
      }
    } else {
      for ( Size i = 0; i < n[0]; i++ ) {
        Cset( dst[ data[0].ctab[i] ], data[0].scale * Re( tmp[i] ), data[0].scale * Im( tmp[i] ) );
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
               Cmplx *tmp,
               FourierOpt opt,
               DJBfftData *data)

{
  Status status;

  while ( count-- ) {

    status = CmplxTransf1( n, src, dst, n[1], tmp, 0, data );
    if ( exception( status ) ) return status;

    for ( Size i = 0; i < n[0];  i++ ) {

      FourierPosCmplx2( n[1], dst + i, n[0], tmp, 1 );

      data[1].fc( tmp );

      DJBforwPosCmplx2( n[1], tmp, dst + i, n[0], data[1].ctab );

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
               Cmplx *tmp,
               FourierOpt opt,
               DJBfftData *data)

{
  Status status;

  while ( count-- ) {

    status = CmplxTransf2( n, src, dst, n[2], tmp, 0, data );
    if ( exception( status ) ) return status;

    for ( Size i = 0; i < n[0] * n[1];  i++ ) {

      FourierPosCmplx2( n[2], dst + i, n[0] * n[1], tmp, 1 );

      data[2].fc( tmp );

      DJBforwPosCmplx2( n[2], tmp, dst + i, n[0] * n[1], data[2].ctab );

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




extern Status DJBfftCmplxTransf
              (const Fourier *fou,
               const void *src,
               void *dst,
               Size count)

{
  DJBfftData *data = fou->data;
  void *tmp = data[0].tmp;
  Status status;

  switch ( fou->dim ) {
    case 0:  status = exception( E_ARGVAL ); break;
    case 1:  status = exception( CmplxTransf1( fou->len, src, dst, count, tmp, fou->opt, data ) ); break;
    case 2:  status = exception( CmplxTransf2( fou->len, src, dst, count, tmp, fou->opt, data ) ); break;
    case 3:  status = exception( CmplxTransf3( fou->len, src, dst, count, tmp, fou->opt, data ) ); break;
    default: status = exception( E_FOURIER_DIM );
  }

  return status;

}


