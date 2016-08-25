/*----------------------------------------------------------------------------*
*
*  fftpackinvrealtransf.c  -  fftpack: fast Fourier transforms with fftpack
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

static Status InvRealTransf1
              (Size n[1],
               const Cmplx *src,
               Real *dst,
               Size count,
               float *wk,
               FourierOpt opt,
               FFTpackData *data)

{

  if ( data[0].n != (int)n[0] ) return exception( E_FFTPACK );

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

  } else {

    while ( count-- ) {

      const Real *s = (const Real *)src;
      dst[0] = ( opt & FourierSetZeromean ) ? 0 : s[0];
      s += 2;
      for ( Size i = 1; i < n[0]; i++ ) {
        dst[i] = *s++;
      }

      rfftb1_( &data[0].n, dst, wk, data[0].wa, data[0].ifac );

      if ( data[0].scale != 1.0 ) {
        Real *d = dst, *de = d + n[0];
        while ( d < de ) {
          *d++ *= data[0].scale;
        }
      }

      src += n[0] / 2 + 1;
      dst += n[0];

    }

  }

  return E_NONE;

}


static Status InvRealTransf2
              (Size n[2],
               const Cmplx *src,
               Real *dst,
               Size count,
               float *wk,
               Cmplx *tmp,
               FourierOpt opt,
               FFTpackData *data)

{

  if ( data[0].n != (int)n[0] ) return exception( E_FFTPACK );
  if ( data[1].n != (int)n[1] ) return exception( E_FFTPACK );

  Size n0inc = n[0] / 2 + 1;

  Real *rtmp = (Real *)tmp;

  while ( count-- ) {

    const Cmplx *s0 = src; Real *d0 = dst;

    if ( opt & FourierDoUncenter ) {
      FourierUncenterCmplx2( n[1], s0++, n0inc, tmp, 1 );
    } else {
      FourierPosCmplx2( n[1], s0++, n0inc, tmp, 1 );
    }

    if ( opt & FourierSetZeromean ) {
      Cset( *tmp, 0, 0 );
    }

    cfftb1_( &data[1].n, rtmp, wk, data[1].wa, data[1].ifac );

    FourierPosReal2( n[1], rtmp, 2, d0++, n[0] );

    for ( Size i = 1; i < ( n[0] + 1 ) / 2;  i++ ) {

      if ( opt & FourierDoUncenter ) {
        FourierUncenterCmplx2( n[1], s0++, n0inc, tmp, 1 );
      } else {
        FourierPosCmplx2( n[1], s0++, n0inc, tmp, 1 );
      }

      cfftb1_( &data[1].n, rtmp, wk, data[1].wa, data[1].ifac );

      FourierPosReal2( n[1], rtmp, 2, d0++, n[0] );
      FourierPosReal2( n[1], rtmp + 1, 2, d0++, n[0] );

    }

    if ( !( n[0] % 2 ) ) {

      if ( opt & FourierDoUncenter ) {
        FourierUncenterCmplx2( n[1], s0, n0inc, tmp, 1 );
      } else {
        FourierPosCmplx2( n[1], s0, n0inc, tmp, 1 );
      }

      cfftb1_( &data[1].n, rtmp, wk, data[1].wa, data[1].ifac );

      FourierPosReal2( n[1], rtmp, 2, d0, n[0] );

    }

    if ( n[0] == 1 ) {

      for ( Size i = 0; i < n[1]; i++ ) {
        *dst++ *= data[0].scale;
      }

    } else {

      for ( Size i = 0; i < n[1]; i++ ) {

        rfftb1_( &data[0].n, dst, wk, data[0].wa, data[0].ifac );

        if ( data[0].scale != 1.0 ) {
          Real *d = dst, *de = d + n[0];
          while ( d < de ) {
            *d++ *= data[0].scale;
          }
        }

        dst += n[0];

      }

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
               float *wk,
               Cmplx *tmp,
               FourierOpt opt,
               FFTpackData *data)

{

  if ( data[0].n != (int)n[0] ) return exception( E_FFTPACK );
  if ( data[1].n != (int)n[1] ) return exception( E_FFTPACK );
  if ( data[2].n != (int)n[2] ) return exception( E_FFTPACK );

  Size n0inc = n[0] / 2 + 1;

  Real *rtmp = (Real *)tmp;

  while ( count-- ) {

    const Cmplx *s0 = src; Real *d0 = dst;

    const Cmplx *s1 = s0; Real *d1 = d0;
    if ( opt & FourierDoUncenter ) s1 += n0inc * ( n[1] / 2 );

    if ( opt & FourierDoUncenter ) {
      FourierUncenterCmplx2( n[2], s1, n0inc * n[1], tmp, 1 );
    } else {
      FourierPosCmplx2( n[2], s1, n0inc * n[1], tmp, 1 );
    }

    if ( opt & FourierSetZeromean ) {
      Cset( *tmp, 0, 0 );
    }

    cfftb1_( &data[2].n, rtmp, wk, data[2].wa, data[2].ifac );

    FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] );

    s1 += n0inc; d1 += n[0];

    for ( Size i = 1; i < ( n[1] + 1 ) / 2;  i++ ) {

      if ( opt & FourierDoUncenter ) {
        FourierUncenterCmplx2( n[2], s1, n0inc * n[1], tmp, 1 );
      } else {
        FourierPosCmplx2( n[2], s1, n0inc * n[1], tmp, 1 );
      }

      cfftb1_( &data[2].n, rtmp, wk, data[2].wa, data[2].ifac );

      FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] ); d1 += n[0];
      FourierPosReal2( n[2], rtmp + 1, 2, d1, n[0] * n[1] ); d1 += n[0];

      s1 += n0inc;

    }

    if ( !( n[1] % 2 ) ) {

      if ( opt & FourierDoUncenter ) s1 = s0;

      if ( opt & FourierDoUncenter ) {
        FourierUncenterCmplx2( n[2], s1, n0inc * n[1], tmp, 1 );
      } else {
        FourierPosCmplx2( n[2], s1, n0inc * n[1], tmp, 1 );
      }

      cfftb1_( &data[2].n, rtmp, wk, data[2].wa, data[2].ifac );

      FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] );

    }

    s0++; d0++;

    for ( Size j = 1; j < ( n[0] + 1 ) / 2;  j++ ) {

      s1 = s0; d1 = d0; 
      if ( opt & FourierDoUncenter ) s1 += n0inc * ( n[1] / 2 );

      for ( Size i = 0; i < n[1];  i++ ) {

        if ( ( opt & FourierDoUncenter ) && ( i == ( n[1] + 1 ) / 2 ) ) s1 = s0;
        if ( opt & FourierDoUncenter ) {
          FourierUncenterCmplx2( n[2], s1, n0inc * n[1], tmp, 1 );
        } else {
          FourierPosCmplx2( n[2], s1, n0inc * n[1], tmp, 1 );
        }

        cfftb1_( &data[2].n, rtmp, wk, data[2].wa, data[2].ifac );

        FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] );
        FourierPosReal2( n[2], rtmp + 1, 2, d1 + 1, n[0] * n[1] );

        s1 += n0inc; d1 += n[0];

      }

      s0++; d0 += 2;

    }

    if ( !( n[0] % 2 ) ) {

      s1 = s0; d1 = d0;
      if ( opt & FourierDoUncenter ) s1 += n0inc * ( n[1] / 2 );

      if ( opt & FourierDoUncenter ) {
        FourierUncenterCmplx2( n[2], s1, n0inc * n[1], tmp, 1 );
      } else {
        FourierPosCmplx2( n[2], s1, n0inc * n[1], tmp, 1 );
      }

      cfftb1_( &data[2].n, rtmp, wk, data[2].wa, data[2].ifac );

      FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] );

      s1 += n0inc; d1 += n[0];

      for ( Size i = 1; i < ( n[1] + 1 ) / 2;  i++ ) {

        if ( opt & FourierDoUncenter ) {
          FourierUncenterCmplx2( n[2], s1, n0inc * n[1], tmp, 1 );
        } else {
          FourierPosCmplx2( n[2], s1, n0inc * n[1], tmp, 1 );
        }

        cfftb1_( &data[2].n, rtmp, wk, data[2].wa, data[2].ifac );

        FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] ); d1 += n[0];
        FourierPosReal2( n[2], rtmp + 1, 2, d1, n[0] * n[1] ); d1 += n[0];

        s1 += n0inc;

      }

      if ( !( n[1] % 2 ) ) {

        if ( opt & FourierDoUncenter ) s1 = s0;

        if ( opt & FourierDoUncenter ) {
          FourierUncenterCmplx2( n[2], s1, n0inc * n[1], tmp, 1 );
        } else {
          FourierPosCmplx2( n[2], s1, n0inc * n[1], tmp, 1 );
        }

        cfftb1_( &data[2].n, rtmp, wk, data[2].wa, data[2].ifac );

        FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] );

      }

    }

    d0 = dst;

    for ( Size j = 0; j < n[2];  j++ ) {

      d1 = d0;

      FourierPosReal2( n[1], d1, n[0], rtmp, 1 );

      rfftb1_( &data[1].n, rtmp, wk, data[1].w2, data[1].ifa2 );

      FourierPosReal2( n[1], rtmp, 1, d1++, n[0] );

      for ( Size i = 1; i < ( n[0] + 1 ) / 2;  i++ ) {

        FourierPosReal2( n[1], d1, n[0], rtmp, 2 );
        FourierPosReal2( n[1], d1 + 1, n[0], rtmp + 1, 2 );

        cfftb1_( &data[1].n, rtmp, wk, data[1].wa, data[1].ifac );

        FourierPosReal2( n[1], rtmp, 2, d1++, n[0] );
        FourierPosReal2( n[1], rtmp + 1, 2, d1++, n[0] );

      }

      if ( !( n[0] % 2 ) ) {

        FourierPosReal2( n[1], d1, n[0], rtmp, 1 );

        rfftb1_( &data[1].n, rtmp, wk, data[1].w2, data[1].ifa2 );

        FourierPosReal2( n[1], rtmp, 1, d1, n[0] );

      }

      d0 += n[0] * n[1];

    }

    if ( n[0] == 1 ) {

      for ( Size j = 0; j < n[1] * n[2]; j++ ) {
        *dst++ *= data[0].scale;
      }

    } else {

      for ( Size j = 0; j < n[1] * n[2];  j++ ) {

        rfftb1_( &data[0].n, dst, wk, data[0].wa, data[0].ifac );

        if ( data[0].scale != 1.0 ) {
          Real *d = dst, *de = d + n[0];
          while ( d < de ) {
            *d++ *= data[0].scale;
          }
        }

        dst += n[0];

      }

    }

    src += n[2] * n[1] * n0inc;

  }

  return E_NONE;

}




extern Status FFTpackInvRealTransf
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
    case 1:  status = exception( InvRealTransf1( fou->len, src, dst, count, wk, fou->opt, data ) ); break;
    case 2:  status = exception( InvRealTransf2( fou->len, src, dst, count, wk, tmp, fou->opt, data ) ); break;
    case 3:  status = exception( InvRealTransf3( fou->len, src, dst, count, wk, tmp, fou->opt, data ) ); break;
    default: status = exception( E_FOURIER_DIM );
  }

  return status;

}



static Status InvImagTransf1
              (Size n[1],
               const Cmplx *src,
               Imag *dst,
               Size count,
               float *wk,
               FourierOpt opt,
               FFTpackData *data)

{

  if ( data[0].n != (int)n[0] ) return exception( E_FFTPACK );

  if ( n[0] == 1 ) {

    if ( opt & FourierSetZeromean ) {

      while ( count-- ) {
        *dst++ = 0;
      }

    } else {

      Real *d = (Real *)dst;
      while ( count-- ) {
        *d++ = data[0].scale * Im( *src++ );
      }

    }

  } else {

    while ( count-- ) {

      Real *d = (Real *)dst;
      *d++ = ( opt & FourierSetZeromean ) ? 0 : Im( *src ); src++;
      for ( Size i = 1; i < ( n[0] + 1 ) / 2; i++ ) {
        *d++ = Im( *src ); *d++ = -Re( *src ); src++;
      }
      if ( !( n[0] % 2 ) ) {
        *d++ = Im( *src++ );
      }

      rfftb1_( &data[0].n, (Real *)dst, wk, data[0].wa, data[0].ifac );

      if ( data[0].scale != 1.0 ) {
        Real *d = (Real *)dst, *de = d + n[0];
        while ( d < de ) {
          *d++ *= data[0].scale;
        }
      }

      dst = (Imag *)d;

    }

  }

  return E_NONE;

}


static Status InvImagTransf2
              (Size n[2],
               const Cmplx *src,
               Imag *dst,
               Size count,
               float *wk,
               Cmplx *tmp,
               FourierOpt opt,
               FFTpackData *data)

{

  if ( data[0].n != (int)n[0] ) return exception( E_FFTPACK );
  if ( data[1].n != (int)n[1] ) return exception( E_FFTPACK );

  Size n0inc = n[0] / 2 + 1;

  Real *rtmp = (Real *)tmp;

  while ( count-- ) {

    const Cmplx *s0 = src; Real *d0 = (Real *)dst;

    FourierDivI2( n[1], s0++, n0inc, tmp, 1 );
    if ( opt & FourierDoUncenter ) {
      FourierUncenterCmplx( n[1], tmp );
    }

    if ( opt & FourierSetZeromean ) {
      Cset( *tmp, 0, 0 );
    }

    cfftb1_( &data[1].n, rtmp, wk, data[1].wa, data[1].ifac );

    FourierPosReal2( n[1], rtmp, 2, d0++, n[0] );

    for ( Size i = 1; i < ( n[0] + 1 ) / 2;  i++ ) {

      FourierDivI2( n[1], s0++, n0inc, tmp, 1 );
      if ( opt & FourierDoUncenter ) {
        FourierUncenterCmplx( n[1], tmp );
      }

      cfftb1_( &data[1].n, rtmp, wk, data[1].wa, data[1].ifac );

      FourierPosReal2( n[1], rtmp, 2, d0++, n[0] );
      FourierPosReal2( n[1], rtmp + 1, 2, d0++, n[0] );

    }

    if ( !( n[0] % 2 ) ) {

      FourierDivI2( n[1], s0, n0inc, tmp, 1 );
      if ( opt & FourierDoUncenter ) {
        FourierUncenterCmplx( n[1], tmp );
      }

      cfftb1_( &data[1].n, rtmp, wk, data[1].wa, data[1].ifac );

      FourierPosReal2( n[1], rtmp, 2, d0, n[0] );

    }

    if ( n[0] == 1 ) {

      Real *d = (Real *)dst;
      for ( Size i = 0; i < n[1]; i++ ) {
        *d++ *= data[0].scale;
      }
      dst = (Imag *)d;

    } else {

      for ( Size i = 0; i < n[1]; i++ ) {

        rfftb1_( &data[0].n, (Real *)dst, wk, data[0].wa, data[0].ifac );

        if ( data[0].scale != 1.0 ) {
          Real *d = (Real *)dst, *de = d + n[0];
          while ( d < de ) {
            *d++ *= data[0].scale;
          }
        }

        dst += n[0];

      }

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
               float *wk,
               Cmplx *tmp,
               FourierOpt opt,
               FFTpackData *data)

{

  if ( data[0].n != (int)n[0] ) return exception( E_FFTPACK );
  if ( data[1].n != (int)n[1] ) return exception( E_FFTPACK );
  if ( data[2].n != (int)n[2] ) return exception( E_FFTPACK );

  Size n0inc = n[0] / 2 + 1;

  Real *rtmp = (Real *)tmp;

  while ( count-- ) {

    const Cmplx *s0 = src; Real *d0 = (Real *)dst;

    const Cmplx *s1 = s0; Real *d1 = d0;
    if ( opt & FourierDoUncenter ) s1 += n0inc * ( n[1] / 2 );

    FourierDivI2( n[2], s1, n0inc * n[1], tmp, 1 );
    if ( opt & FourierDoUncenter ) {
      FourierUncenterCmplx( n[2], tmp );
    }

    if ( opt & FourierSetZeromean ) {
      Cset( *tmp, 0, 0 );
    }

    cfftb1_( &data[2].n, rtmp, wk, data[2].wa, data[2].ifac );

    FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] );

    s1 += n0inc; d1 += n[0];

    for ( Size i = 1; i < ( n[1] + 1 ) / 2;  i++ ) {

      FourierDivI2( n[2], s1, n0inc * n[1], tmp, 1 );
      if ( opt & FourierDoUncenter ) {
        FourierUncenterCmplx( n[2], tmp );
      }

      cfftb1_( &data[2].n, rtmp, wk, data[2].wa, data[2].ifac );

      FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] ); d1 += n[0];
      FourierPosReal2( n[2], rtmp + 1, 2, d1, n[0] * n[1] ); d1 += n[0];

      s1 += n0inc;

    }

    if ( !( n[1] % 2 ) ) {

      if ( opt & FourierDoUncenter ) s1 = s0;

      FourierDivI2( n[2], s1, n0inc * n[1], tmp, 1 );
      if ( opt & FourierDoUncenter ) {
        FourierUncenterCmplx( n[2], tmp );
      }

      cfftb1_( &data[2].n, rtmp, wk, data[2].wa, data[2].ifac );

      FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] );

    }

    s0++; d0++;

    for ( Size j = 1; j < ( n[0] + 1 ) / 2;  j++ ) {

      s1 = s0; d1 = d0; 
      if ( opt & FourierDoUncenter ) s1 += n0inc * ( n[1] / 2 );

      for ( Size i = 0; i < n[1];  i++ ) {

        if ( ( opt & FourierDoUncenter ) && ( i == ( n[1] + 1 ) / 2 ) ) s1 = s0;
        FourierDivI2( n[2], s1, n0inc * n[1], tmp, 1 );
        if ( opt & FourierDoUncenter ) {
          FourierUncenterCmplx( n[2], tmp );
        }

        cfftb1_( &data[2].n, rtmp, wk, data[2].wa, data[2].ifac );

        FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] );
        FourierPosReal2( n[2], rtmp + 1, 2, d1 + 1, n[0] * n[1] );

        s1 += n0inc; d1 += n[0];

      }

      s0++; d0 += 2;

    }

    if ( !( n[0] % 2 ) ) {

      s1 = s0; d1 = d0;
      if ( opt & FourierDoUncenter ) s1 += n0inc * ( n[1] / 2 );

      FourierDivI2( n[2], s1, n0inc * n[1], tmp, 1 );
      if ( opt & FourierDoUncenter ) {
        FourierUncenterCmplx( n[2], tmp );
      }

      cfftb1_( &data[2].n, rtmp, wk, data[2].wa, data[2].ifac );

      FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] );

      s1 += n0inc; d1 += n[0];

      for ( Size i = 1; i < ( n[1] + 1 ) / 2;  i++ ) {

        FourierDivI2( n[2], s1, n0inc * n[1], tmp, 1 );
        if ( opt & FourierDoUncenter ) {
          FourierUncenterCmplx( n[2], tmp );
        }

        cfftb1_( &data[2].n, rtmp, wk, data[2].wa, data[2].ifac );

        FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] ); d1 += n[0];
        FourierPosReal2( n[2], rtmp + 1, 2, d1, n[0] * n[1] ); d1 += n[0];

        s1 += n0inc;

      }

      if ( !( n[1] % 2 ) ) {

        if ( opt & FourierDoUncenter ) s1 = s0;

        FourierDivI2( n[2], s1, n0inc * n[1], tmp, 1 );
        if ( opt & FourierDoUncenter ) {
          FourierUncenterCmplx( n[2], tmp );
        }

        cfftb1_( &data[2].n, rtmp, wk, data[2].wa, data[2].ifac );

        FourierPosReal2( n[2], rtmp, 2, d1, n[0] * n[1] );

      }

    }

    d0 = (Real *)dst;

    for ( Size j = 0; j < n[2];  j++ ) {

      d1 = d0;

      FourierPosReal2( n[1], d1, n[0], rtmp, 1 );

      rfftb1_( &data[1].n, rtmp, wk, data[1].w2, data[1].ifa2 );

      FourierPosReal2( n[1], rtmp, 1, d1++, n[0] );

      for ( Size i = 1; i < ( n[0] + 1 ) / 2;  i++ ) {

        FourierPosReal2( n[1], d1, n[0], rtmp, 2 );
        FourierPosReal2( n[1], d1 + 1, n[0], rtmp + 1, 2 );

        cfftb1_( &data[1].n, rtmp, wk, data[1].wa, data[1].ifac );

        FourierPosReal2( n[1], rtmp, 2, d1++, n[0] );
        FourierPosReal2( n[1], rtmp + 1, 2, d1++, n[0] );

      }

      if ( !( n[0] % 2 ) ) {

        FourierPosReal2( n[1], d1, n[0], rtmp, 1 );

        rfftb1_( &data[1].n, rtmp, wk, data[1].w2, data[1].ifa2 );

        FourierPosReal2( n[1], rtmp, 1, d1, n[0] );

      }

      d0 += n[0] * n[1];

    }

    if ( n[0] == 1 ) {

      Real *d = (Real *)dst;
      for ( Size j = 0; j < n[1] * n[2]; j++ ) {
        *d++ *= data[0].scale;
      }
      dst = (Imag *)d;

    } else {

      for ( Size j = 0; j < n[1] * n[2];  j++ ) {

        rfftb1_( &data[0].n, dst, wk, data[0].wa, data[0].ifac );

        if ( data[0].scale != 1.0 ) {
          Real *d = dst, *de = d + n[0];
          while ( d < de ) {
            *d++ *= data[0].scale;
          }
        }

        dst += n[0];

      }

    }

    src += n[2] * n[1] * n0inc;

  }

  return E_NONE;

}




extern Status FFTpackInvImagTransf
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
    case 1:  status = exception( InvImagTransf1( fou->len, src, dst, count, wk, fou->opt, data ) ); break;
    case 2:  status = exception( InvImagTransf2( fou->len, src, dst, count, wk, tmp, fou->opt, data ) ); break;
    case 3:  status = exception( InvImagTransf3( fou->len, src, dst, count, wk, tmp, fou->opt, data ) ); break;
    default: status = exception( E_FOURIER_DIM );
  }

  return status;

}


