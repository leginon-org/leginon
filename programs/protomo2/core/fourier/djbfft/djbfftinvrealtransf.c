/*----------------------------------------------------------------------------*
*
*  djbfftinvrealtransf.c  -  djbfft: fast Fourier transforms
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

static Status InvRealTransf1
              (Size n[1],
               const Cmplx *src,
               Real *dst,
               Size count,
               Cmplx *tmp,
               FourierOpt opt,
               DJBfftData *data)

{
  Real *rtmp = (Real *)tmp;

  while ( count-- ) {

    DJBbackPosReal( n[0], (const Real *)src, NULL, 2, rtmp, data[0].rtab );

    if ( opt & FourierSetZeromean ) rtmp[0] = 0;

    data[0].br( rtmp );

    DJBunpackReal( n[0], rtmp, dst, data[0].scale );

    src += n[0] / 2 + 1;
    dst += n[0];

  }

  return E_NONE;

}


static Status InvRealTransf2
              (Size n[2],
               const Cmplx *src,
               Real *dst,
               Size count,
               Cmplx *tmp,
               FourierOpt opt,
               DJBfftData *data)

{
  Size n0inc = n[0] / 2 + 1;

  Real *rtmp = (Real *)tmp;
  Cmplx *tmp2 = tmp + n[1]; Real *rtmp2 = (Real *)tmp2;

  while ( count-- ) {

    const Cmplx *s0 = src; Real *d0 = dst;

    if ( opt & FourierDoUncenter ) {
      FourierUncenterCmplx2( n[1], s0++, n0inc, tmp2, 1 );
      DJBbackPosReal( n[1], rtmp2, NULL, 2, rtmp, data[1].rtab );
    } else {
      DJBbackPosReal( n[1], (Real *)s0++, NULL, 2 * n0inc, rtmp, data[1].rtab );
    }

    if ( opt & FourierSetZeromean ) rtmp[0] = 0;

    data[1].br( rtmp );

    DJBunpackReal2( n[1], rtmp, d0, n[0] );

    d0 += 2;

    for ( Size i = 1; i < n[0] / 2;  i++ ) {

      if ( opt & FourierDoUncenter ) {
        FourierUncenterCmplx2( n[1], s0++, n0inc, tmp2, 1 );
        DJBbackPosCmplx2( n[1], tmp2, 1, tmp, data[1].ctab );
      } else {
        DJBbackPosCmplx2( n[1], s0++, n0inc, tmp, data[1].ctab );
      }

      data[1].bc( tmp );

      FourierPosReal2( n[1], rtmp, 2, d0++, n[0] );
      FourierPosReal2( n[1], rtmp + 1, 2, d0++, n[0] );

    }

    d0 = dst + 1;

    if ( opt & FourierDoUncenter ) {
      FourierUncenterCmplx2( n[1], s0, n0inc, tmp2, 1 );
      DJBbackPosReal( n[1], rtmp2, NULL, 2, rtmp, data[1].rtab );
    } else {
      DJBbackPosReal( n[1], (Real *)s0, NULL, 2 * n0inc, rtmp, data[1].rtab );
    }

    data[1].br( rtmp );

    DJBunpackReal2( n[1], rtmp, d0, n[0] );

    for ( Size i = 0; i < n[1]; i++ ) {

      DJBbackPosReal( n[0], dst, dst + 1, 2, rtmp, data[0].rtab );

      data[0].br( rtmp );

      DJBunpackReal( n[0], rtmp, dst, data[0].scale );

      dst += n[0];

    }

    src += n[1] * n0inc;

  }

  return E_NONE;

}


static Status InvRealTransf3
              (Size n[3],
               const Cmplx *src,
               Real *dst,
               Size count,
               Cmplx *tmp,
               FourierOpt opt,
               DJBfftData *data)

{
  Size n0inc = n[0] / 2 + 1;

  Real *rtmp = (Real *)tmp;
  Cmplx *tmp2 = tmp + n[2];

  while ( count-- ) {

    const Cmplx *s0 = src; Real *d0 = dst;

    const Cmplx *s1 = s0; Real *d1 = d0;
    if ( opt & FourierDoUncenter ) s1 += n0inc * ( n[1] / 2 );

    if ( opt & FourierDoUncenter ) {
      FourierUncenterCmplx2( n[2], s1, n0inc * n[1], tmp2, 1 );
      DJBbackPosCmplx2( n[2], tmp2, 1, tmp, data[2].ctab );
    } else {
      DJBbackPosCmplx2( n[2], s1, n0inc * n[1], tmp, data[2].ctab );
    }

    if ( opt & FourierSetZeromean ) {
      Cset( *tmp, 0, 0 );
    }

    data[2].bc( tmp );

    FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] );

    s1 += n0inc; d1 += 2 * n[0];

    for ( Size i = 1; i < ( n[1] + 1 ) / 2;  i++ ) {

      if ( opt & FourierDoUncenter ) {
        FourierUncenterCmplx2( n[2], s1, n0inc * n[1], tmp2, 1 );
        DJBbackPosCmplx2( n[2], tmp2, 1, tmp, data[2].ctab );
      } else {
        DJBbackPosCmplx2( n[2], s1, n0inc * n[1], tmp, data[2].ctab );
      }

      data[2].bc( tmp );

      FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] ); d1 += n[0];
      FourierPosReal2( n[2], rtmp + 1, 2, d1, n[0] * n[1] ); d1 += n[0];

      s1 += n0inc;

    }

    d1 = d0 + n[0];

    if ( opt & FourierDoUncenter ) s1 = s0;

    if ( opt & FourierDoUncenter ) {
      FourierUncenterCmplx2( n[2], s1, n0inc * n[1], tmp2, 1 );
      DJBbackPosCmplx2( n[2], tmp2, 1, tmp, data[2].ctab );
    } else {
      DJBbackPosCmplx2( n[2], s1, n0inc * n[1], tmp, data[2].ctab );
    }

    data[2].bc( tmp );

    FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] );

    s0++; d0 += 2;

    for ( Size j = 1; j < ( n[0] + 1 ) / 2;  j++ ) {

      s1 = s0; d1 = d0; 
      if ( opt & FourierDoUncenter ) s1 += n0inc * ( n[1] / 2 );

      for ( Size i = 0; i < n[1];  i++ ) {

        if ( ( opt & FourierDoUncenter ) && ( i == ( n[1] + 1 ) / 2 ) ) s1 = s0;
        if ( opt & FourierDoUncenter ) {
          FourierUncenterCmplx2( n[2], s1, n0inc * n[1], tmp2, 1 );
          DJBbackPosCmplx2( n[2], tmp2, 1, tmp, data[2].ctab );
        } else {
          DJBbackPosCmplx2( n[2], s1, n0inc * n[1], tmp, data[2].ctab );
        }

        data[2].bc( tmp );

        FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] );
        FourierPosReal2( n[2], rtmp + 1, 2, d1 + 1, n[0] * n[1] );

        s1 += n0inc; d1 += n[0];

      }

      s0++; d0 += 2;

    }

    d0 = dst + 1;

    s1 = s0; d1 = d0;
    if ( opt & FourierDoUncenter ) s1 += n0inc * ( n[1] / 2 );

    if ( opt & FourierDoUncenter ) {
      FourierUncenterCmplx2( n[2], s1, n0inc * n[1], tmp2, 1 );
      DJBbackPosCmplx2( n[2], tmp2, 1, tmp, data[2].ctab );
    } else {
      DJBbackPosCmplx2( n[2], s1, n0inc * n[1], tmp, data[2].ctab );
    }

    data[2].bc( tmp );

    FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] );

    s1 += n0inc; d1 += 2 * n[0];

    for ( Size i = 1; i < ( n[1] + 1 ) / 2;  i++ ) {

      if ( opt & FourierDoUncenter ) {
        FourierUncenterCmplx2( n[2], s1, n0inc * n[1], tmp2, 1 );
        DJBbackPosCmplx2( n[2], tmp2, 1, tmp, data[2].ctab );
      } else {
        DJBbackPosCmplx2( n[2], s1, n0inc * n[1], tmp, data[2].ctab );
      }

      data[2].bc( tmp );

      FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] ); d1 += n[0];
      FourierPosReal2( n[2], rtmp + 1, 2, d1, n[0] * n[1] ); d1 += n[0];

      s1 += n0inc;

    }

    d1 = d0 + n[0];

    if ( opt & FourierDoUncenter ) s1 = s0;

    if ( opt & FourierDoUncenter ) {
      FourierUncenterCmplx2( n[2], s1, n0inc * n[1], tmp2, 1 );
      DJBbackPosCmplx2( n[2], tmp2, 1, tmp, data[2].ctab );
    } else {
      DJBbackPosCmplx2( n[2], s1, n0inc * n[1], tmp, data[2].ctab );
    }

    data[2].bc( tmp );

    FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] );

    d0 = dst;

    for ( Size j = 0; j < n[2];  j++ ) {

      d1 = d0;

      DJBbackPosReal0( n[1], d1, n[0], rtmp, data[1].rtab );

      data[1].br( rtmp );

      DJBunpackReal2( n[1], rtmp, d1++, n[0] );

      DJBbackPosReal0( n[1], d1, n[0], rtmp, data[1].rtab );

      data[1].br( rtmp );

      DJBunpackReal2( n[1], rtmp, d1++, n[0] );

      for ( Size i = 1; i < ( n[0] + 1 ) / 2;  i++ ) {

        DJBbackPosCmplx2( n[1], (Cmplx *)d1, n[0] / 2, tmp, data[1].ctab );

        data[1].bc( tmp );

        FourierPosReal2( n[1], rtmp, 2, d1++, n[0] );
        FourierPosReal2( n[1], rtmp + 1, 2, d1++, n[0] );

      }

      d0 += n[0] * n[1];

    }

    for ( Size j = 0; j < n[1] * n[2];  j++ ) {

      DJBbackPosReal( n[0], dst, dst + 1, 2, rtmp, data[0].rtab );

      data[0].br( rtmp );

      DJBunpackReal( n[0], rtmp, dst, data[0].scale );

      dst += n[0];

    }

    src += n[2] * n[1] * n0inc;

  }

  return E_NONE;

}




extern Status DJBfftInvRealTransf
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
    case 1:  status = exception( InvRealTransf1( fou->len, src, dst, count, tmp, fou->opt, data ) ); break;
    case 2:  status = exception( InvRealTransf2( fou->len, src, dst, count, tmp, fou->opt, data ) ); break;
    case 3:  status = exception( InvRealTransf3( fou->len, src, dst, count, tmp, fou->opt, data ) ); break;
    default: status = exception( E_FOURIER_DIM );
  }

  return status;

}



static Status InvImagTransf1
              (Size n[1],
               const Cmplx *src,
               Imag *dst,
               Size count,
               Cmplx *tmp,
               FourierOpt opt,
               DJBfftData *data)

{
  Real *rtmp = (Real *)tmp;

  while ( count-- ) {

    DJBbackDivIReal( n[0], (const Real *)src, NULL, 2, rtmp, data[0].rtab );

    if ( opt & FourierSetZeromean ) rtmp[0] = 0;

    data[0].br( rtmp );

    DJBunpackReal( n[0], rtmp, (Real *)dst, data[0].scale );

    src += n[0] / 2 + 1;
    dst += n[0];

  }

  return E_NONE;

}


static Status InvImagTransf2
              (Size n[2],
               const Cmplx *src,
               Imag *dst,
               Size count,
               Cmplx *tmp,
               FourierOpt opt,
               DJBfftData *data)

{
  Size n0inc = n[0] / 2 + 1;

  Real *rtmp = (Real *)tmp;
  Cmplx *tmp2 = tmp + n[1]; Real *rtmp2 = (Real *)tmp2;

  while ( count-- ) {

    const Cmplx *s0 = src; Real *d0 = (Real *)dst;

    if ( opt & FourierDoUncenter ) {
      FourierUncenterCmplx2( n[1], s0++, n0inc, tmp2, 1 );
      DJBbackDivIReal( n[1], rtmp2, NULL, 2, rtmp, data[1].rtab );
    } else {
      DJBbackDivIReal( n[1], (Real *)s0++, NULL, 2 * n0inc, rtmp, data[1].rtab );
    }

    if ( opt & FourierSetZeromean ) rtmp[0] = 0;

    data[1].br( rtmp );

    DJBunpackReal2( n[1], rtmp, d0, n[0] );

    d0 += 2;

    for ( Size i = 1; i < n[0] / 2;  i++ ) {

      if ( opt & FourierDoUncenter ) {
        FourierUncenterCmplx2( n[1], s0++, n0inc, tmp2, 1 );
        DJBbackDivICmplx2( n[1], tmp2, 1, tmp, data[1].ctab );
      } else {
        DJBbackDivICmplx2( n[1], s0++, n0inc, tmp, data[1].ctab );
      }

      data[1].bc( tmp );

      FourierPosReal2( n[1], rtmp, 2, d0++, n[0] );
      FourierPosReal2( n[1], rtmp + 1, 2, d0++, n[0] );

    }

    d0 = (Real *)dst + 1;

    if ( opt & FourierDoUncenter ) {
      FourierUncenterCmplx2( n[1], s0, n0inc, tmp2, 1 );
      DJBbackDivIReal( n[1], rtmp2, NULL, 2, rtmp, data[1].rtab );
    } else {
      DJBbackDivIReal( n[1], (Real *)s0, NULL, 2 * n0inc, rtmp, data[1].rtab );
    }

    data[1].br( rtmp );

    DJBunpackReal2( n[1], rtmp, d0, n[0] );

    for ( Size i = 0; i < n[1]; i++ ) {

      DJBbackPosReal( n[0], (Real *)dst, (Real *)dst + 1, 2, rtmp, data[0].rtab );

      data[0].br( rtmp );

      DJBunpackReal( n[0], rtmp, (Real *)dst, data[0].scale );

      dst += n[0];

    }

    src += n[1] * n0inc;

  }

  return E_NONE;

}


static Status InvImagTransf3
              (Size n[3],
               const Cmplx *src,
               Imag *dst,
               Size count,
               Cmplx *tmp,
               FourierOpt opt,
               DJBfftData *data)

{
  Size n0inc = n[0] / 2 + 1;

  Real *rtmp = (Real *)tmp;
  Cmplx *tmp2 = tmp + n[2];

  while ( count-- ) {

    const Cmplx *s0 = src; Real *d0 = (Real *)dst;

    const Cmplx *s1 = s0; Real *d1 = d0;
    if ( opt & FourierDoUncenter ) s1 += n0inc * ( n[1] / 2 );

    if ( opt & FourierDoUncenter ) {
      FourierUncenterCmplx2( n[2], s1, n0inc * n[1], tmp2, 1 );
      DJBbackDivICmplx2( n[2], tmp2, 1, tmp, data[2].ctab );
    } else {
      DJBbackDivICmplx2( n[2], s1, n0inc * n[1], tmp, data[2].ctab );
    }

    if ( opt & FourierSetZeromean ) {
      Cset( *tmp, 0, 0 );
    }

    data[2].bc( tmp );

    FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] );

    s1 += n0inc; d1 += 2 * n[0];

    for ( Size i = 1; i < ( n[1] + 1 ) / 2;  i++ ) {

      if ( opt & FourierDoUncenter ) {
        FourierUncenterCmplx2( n[2], s1, n0inc * n[1], tmp2, 1 );
        DJBbackDivICmplx2( n[2], tmp2, 1, tmp, data[2].ctab );
      } else {
        DJBbackDivICmplx2( n[2], s1, n0inc * n[1], tmp, data[2].ctab );
      }

      data[2].bc( tmp );

      FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] ); d1 += n[0];
      FourierPosReal2( n[2], rtmp + 1, 2, d1, n[0] * n[1] ); d1 += n[0];

      s1 += n0inc;

    }

    d1 = d0 + n[0];

    if ( opt & FourierDoUncenter ) s1 = s0;

    if ( opt & FourierDoUncenter ) {
      FourierUncenterCmplx2( n[2], s1, n0inc * n[1], tmp2, 1 );
      DJBbackDivICmplx2( n[2], tmp2, 1, tmp, data[2].ctab );
    } else {
      DJBbackDivICmplx2( n[2], s1, n0inc * n[1], tmp, data[2].ctab );
    }

    data[2].bc( tmp );

    FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] );

    s0++; d0 += 2;

    for ( Size j = 1; j < ( n[0] + 1 ) / 2;  j++ ) {

      s1 = s0; d1 = d0; 
      if ( opt & FourierDoUncenter ) s1 += n0inc * ( n[1] / 2 );

      for ( Size i = 0; i < n[1];  i++ ) {

        if ( ( opt & FourierDoUncenter ) && ( i == ( n[1] + 1 ) / 2 ) ) s1 = s0;
        if ( opt & FourierDoUncenter ) {
          FourierUncenterCmplx2( n[2], s1, n0inc * n[1], tmp2, 1 );
          DJBbackDivICmplx2( n[2], tmp2, 1, tmp, data[2].ctab );
        } else {
          DJBbackDivICmplx2( n[2], s1, n0inc * n[1], tmp, data[2].ctab );
        }

        data[2].bc( tmp );

        FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] );
        FourierPosReal2( n[2], rtmp + 1, 2, d1 + 1, n[0] * n[1] );

        s1 += n0inc; d1 += n[0];

      }

      s0++; d0 += 2;

    }

    d0 = (Real *)dst + 1;

    s1 = s0; d1 = d0;
    if ( opt & FourierDoUncenter ) s1 += n0inc * ( n[1] / 2 );

    if ( opt & FourierDoUncenter ) {
      FourierUncenterCmplx2( n[2], s1, n0inc * n[1], tmp2, 1 );
      DJBbackDivICmplx2( n[2], tmp2, 1, tmp, data[2].ctab );
    } else {
      DJBbackDivICmplx2( n[2], s1, n0inc * n[1], tmp, data[2].ctab );
    }

    data[2].bc( tmp );

    FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] );

    s1 += n0inc; d1 += 2 * n[0];

    for ( Size i = 1; i < ( n[1] + 1 ) / 2;  i++ ) {

      if ( opt & FourierDoUncenter ) {
        FourierUncenterCmplx2( n[2], s1, n0inc * n[1], tmp2, 1 );
        DJBbackDivICmplx2( n[2], tmp2, 1, tmp, data[2].ctab );
      } else {
        DJBbackDivICmplx2( n[2], s1, n0inc * n[1], tmp, data[2].ctab );
      }

      data[2].bc( tmp );

      FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] ); d1 += n[0];
      FourierPosReal2( n[2], rtmp + 1, 2, d1, n[0] * n[1] ); d1 += n[0];

      s1 += n0inc;

    }

    d1 = d0 + n[0];

    if ( opt & FourierDoUncenter ) s1 = s0;

    if ( opt & FourierDoUncenter ) {
      FourierUncenterCmplx2( n[2], s1, n0inc * n[1], tmp2, 1 );
      DJBbackDivICmplx2( n[2], tmp2, 1, tmp, data[2].ctab );
    } else {
      DJBbackDivICmplx2( n[2], s1, n0inc * n[1], tmp, data[2].ctab );
    }

    data[2].bc( tmp );

    FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] );

    d0 = (Real *)dst;

    for ( Size j = 0; j < n[2];  j++ ) {

      d1 = d0;

      DJBbackPosReal0( n[1], d1, n[0], rtmp, data[1].rtab );

      data[1].br( rtmp );

      DJBunpackReal2( n[1], rtmp, d1++, n[0] );

      DJBbackPosReal0( n[1], d1, n[0], rtmp, data[1].rtab );

      data[1].br( rtmp );

      DJBunpackReal2( n[1], rtmp, d1++, n[0] );

      for ( Size i = 1; i < ( n[0] + 1 ) / 2;  i++ ) {

        DJBbackPosCmplx2( n[1], (Cmplx *)d1, n[0] / 2, tmp, data[1].ctab );

        data[1].bc( tmp );

        FourierPosReal2( n[1], rtmp, 2, d1++, n[0] );
        FourierPosReal2( n[1], rtmp + 1, 2, d1++, n[0] );

      }

      d0 += n[0] * n[1];

    }

    for ( Size j = 0; j < n[1] * n[2];  j++ ) {

      DJBbackPosReal( n[0], (Real *)dst, (Real *)dst + 1, 2, rtmp, data[0].rtab );

      data[0].br( rtmp );

      DJBunpackReal( n[0], rtmp, (Real *)dst, data[0].scale );

      dst += n[0];

    }

    src += n[2] * n[1] * n0inc;

  }

  return E_NONE;

}




extern Status DJBfftInvImagTransf
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
    case 1:  status = exception( InvImagTransf1( fou->len, src, dst, count, tmp, fou->opt, data ) ); break;
    case 2:  status = exception( InvImagTransf2( fou->len, src, dst, count, tmp, fou->opt, data ) ); break;
    case 3:  status = exception( InvImagTransf3( fou->len, src, dst, count, tmp, fou->opt, data ) ); break;
    default: status = exception( E_FOURIER_DIM );
  }

  return status;

}


