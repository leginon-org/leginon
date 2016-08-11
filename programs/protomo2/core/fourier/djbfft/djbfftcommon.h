/*----------------------------------------------------------------------------*
*
*  djbfftcommon.h  -  djbfft: fast Fourier transforms
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef djbfftcommon_h_
#define djbfftcommon_h_

#include "djbfft.h"
#include "djbfftdefs.h"
#include "fouriercommon.h"


/* types */

typedef struct {
  void (*fr)( Real32 * );
  void (*br)( Real32 * );
  void (*fc)( Cmplx32 * );
  void (*bc)( Cmplx32 * );
  unsigned int *rtab;
  unsigned int *ctab;
  Cmplx *tmp;
  double scale;
} DJBfftData;


/* macros */

#define DJBpackReal( n, src, dst, scale )                                \
  {                                                                      \
    Size ns = ( n );                                                     \
    const Real *s = ( src ), *sh = s + ns / 2, *se = sh;                 \
    Real *d = ( dst );                                                   \
    if ( scale == 1.0 ) {                                                \
      while ( s < se ) {                                                 \
        *d++ = *s++; *d++ = *sh++;                                       \
      }                                                                  \
    } else {                                                             \
      while ( s < se ) {                                                 \
        *d++ = scale * *s++; *d++ = scale * *sh++;                       \
      }                                                                  \
    }                                                                    \
  }                                                                      \

#define DJBpackReal2( n, src, srcinc, dst )                              \
  {                                                                      \
    Size ns = ( n ), si = ( srcinc );                                    \
    const Real *s = ( src ), *sh = s + ( ns / 2 ) * si, *se = sh;        \
    Real *d = ( dst );                                                   \
    while ( s < se ) {                                                   \
      *d++ = *s; s += si;                                                \
      *d++ = *sh; sh += si;                                              \
    }                                                                    \
  }                                                                      \

#define DJBunpackReal( n, src, dst, scale )                              \
  {                                                                      \
    Size nd = ( n );                                                     \
    const Real *s = ( src );                                             \
    Real *d = ( dst ), *dh = d + nd / 2, *de = dh;                       \
    if ( scale == 1.0 ) {                                                \
      while ( d < de ) {                                                 \
        *d++ = *s++; *dh++ = *s++;                                       \
      }                                                                  \
    } else {                                                             \
      while ( d < de ) {                                                 \
        *d++ = scale * *s++; *dh++ = scale * *s++;                       \
      }                                                                  \
    }                                                                    \
  }                                                                      \

#define DJBunpackReal2( n, src, dst, dstinc )                            \
  {                                                                      \
    Size nd = ( n ), di = ( dstinc );                                    \
    const Real *s = ( src );                                             \
    Real *d = ( dst ), *dh = d + ( nd / 2 ) * di, *de = dh;              \
    while ( d < de ) {                                                   \
      *d = *s++; d += di;                                                \
      *dh = *s++; dh += di;                                              \
    }                                                                    \
  }                                                                      \

#define DJBforwPosReal( n, src, dst, tab )                               \
  {                                                                      \
    Size nd = ( n );                                                     \
    const Real *s = ( src ), *se = s + nd; Real *d = ( dst );            \
    const unsigned int *t = tab;                                         \
    d[0] = *s++; d[1] = 0;                                               \
    d[nd] = *s++; d[nd+1] = 0;                                           \
    while ( s < se ) {                                                   \
      t += 2;                                                            \
      if ( *t < nd / 2 ) {                                               \
        Size i = *t + *t; d[i++] = *s++; d[i] = *s++;                    \
      } else {                                                           \
        Size i = nd - *t; i += i; d[i++] = *s++; d[i] = -*s++;           \
      }                                                                  \
    }                                                                    \
  }                                                                      \

#define DJBforwPosReal2( n, src, dst, dstinc, tab )                      \
  {                                                                      \
    Size nd = ( n ), di = ( dstinc );                                    \
    const Real *s = ( src ), *se = s + nd; Real *d = ( dst );            \
    const unsigned int *t = tab;                                         \
    Size i = ( nd / 2 ) * di;                                            \
    d[0] = *s++; d[1] = 0;                                               \
    d[i++] = *s++; d[i] = 0;                                             \
    while ( s < se ) {                                                   \
      t += 2;                                                            \
      if ( *t < nd / 2 ) {                                               \
        Size i = *t * di; d[i++] = *s++; d[i] = *s++;                    \
      } else {                                                           \
        Size i = ( nd - *t ) * di; d[i++] = *s++; d[i] = -*s++;          \
      }                                                                  \
    }                                                                    \
  }                                                                      \

#define DJBforwMulIReal( n, src, dst, tab )                              \
  {                                                                      \
    Size nd = ( n );                                                     \
    const Real *s = ( src ), *se = s + nd; Real *d = ( dst );            \
    const unsigned int *t = tab;                                         \
    d[0] = 0; d[1] = *s++;                                               \
    d[nd] = 0; d[nd+1] = *s++;                                           \
    while ( s < se ) {                                                   \
      Real re = *s++; Real im = *s++;                                    \
      t += 2;                                                            \
      if ( *t < nd / 2 ) {                                               \
        Size i = *t + *t; d[i++] = -im; d[i] = re;                       \
      } else {                                                           \
        Size i = nd - *t; i += i; d[i++] = im; d[i] = re;                \
      }                                                                  \
    }                                                                    \
  }                                                                      \

#define DJBforwMulIReal2( n, src, dst, dstinc, tab )                     \
  {                                                                      \
    Size nd = ( n ), di = ( dstinc );                                    \
    const Real *s = ( src ), *se = s + nd; Real *d = ( dst );            \
    const unsigned int *t = tab;                                         \
    Size i = ( nd / 2 ) * di;                                            \
    d[0] = 0; d[1] = *s++;                                               \
    d[i++] = 0; d[i] = *s++;                                             \
    while ( s < se ) {                                                   \
      Real re = *s++; Real im = *s++;                                    \
      t += 2;                                                            \
      if ( *t < nd / 2 ) {                                               \
        Size i = *t * di; d[i++] = -im; d[i] = re;                       \
      } else {                                                           \
        Size i = ( nd - *t ) * di; d[i++] = im; d[i] = re;               \
      }                                                                  \
    }                                                                    \
  }                                                                      \

#define DJBbackPosReal( n, src, srcn, srcinc, dst, tab )                 \
  {                                                                      \
    Size ns = ( n ), si = ( srcinc );                                    \
    const Real *s = ( src ), *sn = ( srcn );                             \
    Real *d = ( dst ), *de = d + ns;                                     \
    const unsigned int *t = tab;                                         \
    *d++ = s[0];                                                         \
    *d++ = ( sn == NULL ) ? s[(ns/2)*si] : *sn;                          \
    while ( d < de ) {                                                   \
      t += 2;                                                            \
      if ( *t < ns / 2 ) {                                               \
        Size i = *t * si; *d++ = 2 * s[i++]; *d++ = 2 * s[i];            \
      } else {                                                           \
        Size i = ( ns - *t ) * si; *d++ = 2 * s[i++]; *d++ = -2 * s[i];  \
      }                                                                  \
    }                                                                    \
  }                                                                      \

#define DJBbackPosReal0( n, src, srcinc, dst, tab )                      \
  {                                                                      \
    Size ns = ( n ), ii = ( srcinc ), si = 2 * ii;                       \
    const Real *s = ( src );                                             \
    Real *d = ( dst ), *de = d + ns;                                     \
    const unsigned int *t = tab;                                         \
    *d++ = s[0]; *d++ = s[ii];                                           \
    while ( d < de ) {                                                   \
      t += 2;                                                            \
      if ( *t < ns / 2 ) {                                               \
        Size i = *t * si; *d++ = 2 * s[i]; *d++ = 2 * s[i+ii];           \
      } else {                                                           \
        Size i = ( ns - *t ) * si; *d++ = 2 * s[i]; *d++ = -2 * s[i+ii]; \
      }                                                                  \
    }                                                                    \
  }                                                                      \

#define DJBbackDivIReal( n, src, srcn, srcinc, dst, tab )                \
  {                                                                      \
    Size ns = ( n ), si = ( srcinc );                                    \
    const Real *s = ( src ), *sn = ( srcn );                             \
    Real *d = ( dst ), *de = d + ns;                                     \
    const unsigned int *t = tab;                                         \
    *d++ = s[1];                                                         \
    *d++ = ( sn == NULL ) ? s[(ns/2)*si+1] : *sn;                        \
    while ( d < de ) {                                                   \
      Real re, im;                                                       \
      t += 2;                                                            \
      if ( *t < ns / 2 ) {                                               \
        Size i = *t * si; im = -2 * s[i++]; re = 2 * s[i];               \
      } else {                                                           \
        Size i = ( ns - *t ) * si; im = 2 * s[i++]; re = 2 * s[i];       \
      }                                                                  \
      *d++ = re; *d++ = im;                                              \
    }                                                                    \
  }                                                                      \

#define DJBforwPosCmplx2( n, src, dst, dstinc, tab )                     \
  {                                                                      \
    Size nd = ( n ), di = ( dstinc );                                    \
    const Cmplx *s = ( src ); Cmplx *d = ( dst );                        \
    const unsigned int *t = tab;                                         \
    for ( Size i = 0; i < nd; i++ ) {                                    \
      d[t[i]*di] = s[i];                                                 \
    }                                                                    \
  }                                                                      \

#define DJBbackPosCmplx2( n, src, srcinc, dst, tab )                     \
  {                                                                      \
    Size ns = ( n ), si = ( srcinc );                                    \
    const Cmplx *s = ( src ); Cmplx *d = ( dst );                        \
    const unsigned int *t = tab;                                         \
    for ( Size i = 0; i < ns; i++ ) {                                    \
      d[i] = s[t[i]*si];                                                 \
    }                                                                    \
  }                                                                      \

#define DJBforwMulICmplx2( n, src, dst, dstinc, tab )                    \
  {                                                                      \
    Size nd = ( n ), di = ( dstinc );                                    \
    const Cmplx *s = ( src ); Cmplx *d = ( dst );                        \
    const unsigned int *t = tab;                                         \
    for ( Size i = 0; i < nd; i++ ) {                                    \
      Real re = Re( s[i] ), im = Im( s[i] );                             \
      Cset( d[t[i]*di], -im, re );                                       \
    }                                                                    \
  }                                                                      \

#define DJBbackDivICmplx2( n, src, srcinc, dst, tab )                    \
  {                                                                      \
    Size ns = ( n ), si = ( srcinc );                                    \
    const Cmplx *s = ( src ); Cmplx *d = ( dst );                        \
    const unsigned int *t = tab;                                         \
    for ( Size i = 0; i < ns; i++ ) {                                    \
      Cmplx sc = s[t[i]*si];                                             \
      Cset( d[i], Im( sc ), -Re( sc ) );                                 \
    }                                                                    \
  }                                                                      \


/* prototypes */

extern Status DJBfftInit
              (Fourier *fou,
               Status *stat);

extern Status DJBfftFinal
              (Fourier *fou);


#endif
