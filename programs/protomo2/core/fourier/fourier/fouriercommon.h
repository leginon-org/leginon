/*----------------------------------------------------------------------------*
*
*  fouriercommon.h  -  fourier: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef fouriercommon_h_
#define fouriercommon_h_

#include "fourier.h"
#include "fouriermode.h"


/* configuration */

#define FourierDimSym 5
#define FourierDimSeq 3


/* types */

typedef enum {
  FourierSetZeromean = 0x0100,
  FourierSetZeroorig = 0x0200,
  FourierDoCenter    = 0x0400,
  FourierDoUncenter  = 0x0800,
  FourierMulI1       = 0x1000,
  FourierMulI2       = 0x2000,
  FourierMulI3       = 0x4000,
  FourierOptMask     = 0x0000ff,
} FourierOpt2;

typedef struct {
  int forwexp;
  int backexp;
  Bool forwnorm;
  Bool backnorm;
} FourierConvention;

typedef struct {
  const char *ident;
  FourierConvention conv;
  Status (*init)( Fourier *, Status * );
  Status (*final)( Fourier * );
  Status (*transf[2][FourierDimSym][FourierDimSeq])( const Fourier *, const void *, void *, Size );
} FourierVersion;

struct _Fourier {
  Size dim;
  Size *len;
  Size seqlen;
  Size srcsize;
  Size dstsize;
  FourierOpt opt;
  FourierMode mode;
  const FourierVersion *vers;
  Size seq;
  Size sym;
  void *data;
  Size tmpsize;
};

typedef struct {
  const Fourier *fou;
  const void *src;
  Size count;
  void *tmp;
} FourierArg;


/* macros */

#define FourierCheck( f, m )                                                   \
  ( ( ( ( f )->mode & FourierModeMask ) == ( m ) ) ? E_NONE : E_FOURIER_MODE )

#define FourierNegReal( n, dst, dstinc )                                       \
  {                                                                            \
    Size di = ( dstinc );                                                      \
    Real *d = ( dst ), *de = d + ( n ) * di;                                   \
    while ( d < de ) {                                                         \
      *d = -*d; d += di;                                                       \
    }                                                                          \
  }                                                                            \

#define FourierNegCmplx( n, dst, dstinc )                                      \
  {                                                                            \
    Size di = ( dstinc );                                                      \
    Cmplx *d = ( dst ), *de = d + ( n ) * di;                                  \
    while ( d < de ) {                                                         \
      Real re = Re( *d ), im = Im( *d );                                       \
      Cset( *d, -re, -im ); d += di;                                           \
    }                                                                          \
  }                                                                            \

#define FourierMulI( n, dst, dstinc )                                          \
  {                                                                            \
    Size di = ( dstinc );                                                      \
    Cmplx *d = ( dst ), *de = d + ( n ) * di;                                  \
    while ( d < de ) {                                                         \
      Real re = Re( *d ), im = Im( *d );                                       \
      Cset( *d, -im, re ); d += di;                                            \
    }                                                                          \
  }                                                                            \

#define FourierDivI( n, dst, dstinc )                                          \
  {                                                                            \
    Size di = ( dstinc );                                                      \
    Cmplx *d = ( dst ), *de = d + ( n ) * di;                                  \
    while ( d < de ) {                                                         \
      Real re = Re( *d ), im = Im( *d );                                       \
      Cset( *d, im, -re ); d += di;                                            \
    }                                                                          \
  }                                                                            \

#define FourierPosReal2( n, src, srcinc, dst, dstinc )                         \
  {                                                                            \
    Size si = ( srcinc ), di = ( dstinc );                                     \
    const Real *s = ( src );                                                   \
    Real *d = ( dst ), *de = d + ( n ) * di;                                   \
    while ( d < de ) {                                                         \
      *d = *s;                                                                 \
      d += di; s += si;                                                        \
    }                                                                          \
  }                                                                            \

#define FourierPosCmplx2( n, src, srcinc, dst, dstinc )                        \
  {                                                                            \
    Size si = ( srcinc ), di = ( dstinc );                                     \
    const Cmplx  *s = ( src );                                                 \
    Cmplx *d = ( dst ), *de = d + ( n ) * di;                                  \
    while ( d < de ) {                                                         \
      *d = *s;                                                                 \
      d += di; s += si;                                                        \
    }                                                                          \
  }                                                                            \

#define FourierNegReal2( n, src, srcinc, dst, dstinc )                         \
  {                                                                            \
    Size si = ( srcinc ), di = ( dstinc );                                     \
    const Real *s = ( src );                                                   \
    Real *d = ( dst ), *de = d + ( n ) * di;                                   \
    while ( d < de ) {                                                         \
      *d = -*s;                                                                \
      d += di; s += si;                                                        \
    }                                                                          \
  }                                                                            \

#define FourierNegCmplx2( n, src, srcinc, dst, dstinc )                        \
  {                                                                            \
    Size si = ( srcinc ), di = ( dstinc );                                     \
    const Cmplx  *s = ( src );                                                 \
    Cmplx *d = ( dst ), *de = d + ( n ) * di;                                  \
    while ( d < de ) {                                                         \
      Real re = Re( *s ), im = Im( *s );                                       \
      Cset( *d, -re, -im );                                                    \
      d += di; s += si;                                                        \
    }                                                                          \
  }                                                                            \

#define FourierMulI2( n, src, srcinc, dst, dstinc )                            \
  {                                                                            \
    Size si = ( srcinc ), di = ( dstinc );                                     \
    const Cmplx  *s = ( src );                                                 \
    Cmplx *d = ( dst ), *de = d + ( n ) * di;                                  \
    while ( d < de ) {                                                         \
      Real re = Re( *s ), im = Im( *s );                                       \
      Cset( *d, -im, re );                                                     \
      d += di; s += si;                                                        \
    }                                                                          \
  }                                                                            \

#define FourierDivI2( n, src, srcinc, dst, dstinc )                            \
  {                                                                            \
    Size si = ( srcinc ), di = ( dstinc );                                     \
    const Cmplx  *s = ( src );                                                 \
    Cmplx *d = ( dst ), *de = d + ( n ) * di;                                  \
    while ( d < de ) {                                                         \
      Real re = Re( *s ), im = Im( *s );                                       \
      Cset( *d, im, -re );                                                     \
      d += di; s += si;                                                        \
    }                                                                          \
  }                                                                            \

#define FourierExtRealEven( ndst, dst, dstinc )                                \
  {                                                                            \
    Size di = ( dstinc );                                                      \
    Real *dp = ( dst );                                                        \
    Real *dn = dp + ( ndst ) * di;                                             \
    dp += di; dn -= di;                                                        \
    while ( dp < dn ) {                                                        \
      *dn = *dp; dn -= di; dp += di;                                           \
    }                                                                          \
  }                                                                            \

#define FourierExtRealOdd( ndst, dst, dstinc )                                 \
  {                                                                            \
    Size di = ( dstinc );                                                      \
    Real *dp = ( dst );                                                        \
    Real *dn = dp + ( ndst ) * di;                                             \
    if ( dp < dn ) {                                                           \
      *dp = 0; dp += di; dn -= di;                                             \
    }                                                                          \
    while ( dp < dn ) {                                                        \
      *dn = -*dp; dn -= di; dp += di;                                          \
    }                                                                          \
    if ( dp == dn ) {                                                          \
      *dp = 0;                                                                 \
    }                                                                          \
  }                                                                            \

#define FourierExtCmplxHerm( ndst, dst, dstinc )                               \
  {                                                                            \
    Size di = ( dstinc );                                                      \
    Cmplx *dp = ( dst );                                                       \
    Cmplx *dn = dp + ( ndst ) * di;                                            \
    if ( dp < dn ) {                                                           \
      Real re = Re( *dp );                                                     \
      Cset( *dp, re, 0 );                                                      \
      dp += di; dn -= di;                                                      \
    }                                                                          \
    while ( dp < dn ) {                                                        \
      Real re = Re( *dp ), im = Im( *dp );                                     \
      Cset( *dn, re, -im );                                                    \
      dn -= di; dp += di;                                                      \
    }                                                                          \
    if ( dp == dn ) {                                                          \
      Real re = Re( *dp );                                                     \
      Cset( *dp, re, 0 );                                                      \
    }                                                                          \
  }                                                                            \

#define FourierExtCmplxAHerm( ndst, dst, dstinc )                              \
  {                                                                            \
    Size di = ( dstinc );                                                      \
    Cmplx *dp = ( dst );                                                       \
    Cmplx *dn = dp + ( ndst ) * di;                                            \
    if ( dp < dn ) {                                                           \
      Real im = Im( *dp );                                                     \
      Cset( *dp, 0, im );                                                      \
      dp += di; dn -= di;                                                      \
    }                                                                          \
    while ( dp < dn ) {                                                        \
      Real re = Re( *dp ), im = Im( *dp );                                     \
      Cset( *dn, -re, im );                                                    \
      dn -= di; dp += di;                                                      \
    }                                                                          \
    if ( dp == dn ) {                                                          \
      Real im = Im( *dp );                                                     \
      Cset( *dp, 0, im );                                                      \
    }                                                                          \
  }                                                                            \

#define FourierExtRealEven2( nsrc, src, srcinc, dst, dstinc )                  \
  {                                                                            \
    Size si = ( srcinc ), di = ( dstinc );                                     \
    const Real *sp = ( src );                                                  \
    Real *dp = ( dst );                                                        \
    Real *dn = dp + ( nsrc ) * di;                                             \
    if ( dp < dn ) {                                                           \
      *dp = *sp; dp += di; sp += si; dn -= di;                                 \
    }                                                                          \
    while ( dp < dn ) {                                                        \
      *dn = *sp; dn -= di;                                                     \
      *dp = *sp; dp += di; sp += si;                                           \
    }                                                                          \
    if ( dp == dn ) {                                                          \
      *dp = *sp;                                                               \
    }                                                                          \
  }                                                                            \

#define FourierExtRealOdd2( nsrc, src, srcinc, dst, dstinc )                   \
  {                                                                            \
    Size si = ( srcinc ), di = ( dstinc );                                     \
    const Real *sp = ( src );                                                  \
    Real *dp = ( dst );                                                        \
    Real *dn = dp + ( nsrc ) * di;                                             \
    if ( dp < dn ) {                                                           \
      *dp = 0; dp += di; sp += si; dn -= di;                                   \
    }                                                                          \
    while ( dp < dn ) {                                                        \
      *dn = -*sp; dn -= di;                                                    \
      *dp =  *sp; dp += di; sp += si;                                          \
    }                                                                          \
    if ( dp == dn ) {                                                          \
      *dp = *sp;                                                               \
    }                                                                          \
  }                                                                            \

#define FourierExtCmplxHerm2( nsrc, src, srcinc, dst, dstinc )                 \
  {                                                                            \
    Size si = ( srcinc ), di = ( dstinc );                                     \
    const Cmplx *sp = ( src );                                                 \
    Cmplx *dp = ( dst );                                                       \
    Cmplx *dn = dp + ( nsrc ) * di;                                            \
    if ( dp < dn ) {                                                           \
      Real re = Re( *sp ); sp += si;                                           \
      Cset( *dp, re, 0 ); dp += di; dn -= di;                                  \
    }                                                                          \
    while ( dp < dn ) {                                                        \
      Real re = Re( *sp ), im = Im( *sp ); sp += si;                           \
      Cset( *dn, re, -im ); dn -= di;                                          \
      Cset( *dp, re,  im ); dp += di;                                          \
    }                                                                          \
    if ( dp == dn ) {                                                          \
      Real re = Re( *sp );                                                     \
      Cset( *dp, re, 0 );                                                      \
    }                                                                          \
  }                                                                            \

#define FourierExtCmplxAHerm2( nsrc, src, srcinc, dst, dstinc )                \
  {                                                                            \
    Size si = ( srcinc ), di = ( dstinc );                                     \
    const Cmplx *sp = ( src );                                                 \
    Cmplx *dp = ( dst );                                                       \
    Cmplx *dn = dp + ( nsrc ) * di;                                            \
    if ( dp < dn ) {                                                           \
      Real im = Im( *sp ); sp += si;                                           \
      Cset( *dp, 0, im ); dp += di; dn -= di;                                  \
    }                                                                          \
    while ( dp < dn ) {                                                        \
      Real re = Re( *sp ), im = Im( *sp ); sp += si;                           \
      Cset( *dn, -re, im ); dn -= di;                                          \
      Cset( *dp,  re, im ); dp += di;                                          \
    }                                                                          \
    if ( dp == dn ) {                                                          \
      Real im = Im( *sp );                                                     \
      Cset( *dp, 0, im );                                                      \
    }                                                                          \
  }                                                                            \

#define FourierExtRealEven3( nsrc, src, srcn, srcinc, dst, dstinc )            \
  {                                                                            \
    Size si = ( srcinc ), di = ( dstinc );                                     \
    const Real *sp = ( src ), *sn = ( srcn );                                  \
    Real *dp = ( dst );                                                        \
    Real *dn = dp + ( nsrc ) * di;                                             \
    if ( dp < dn ) {                                                           \
      *dp = *sp; dp += di; sp += si; dn -= di; sn += si;                       \
    }                                                                          \
    while ( dp < dn ) {                                                        \
      *dn = *sn; dn -= di; sn += si;                                           \
      *dp = *sp; dp += di; sp += si;                                           \
    }                                                                          \
    if ( dp == dn ) {                                                          \
      *dp = *sp;                                                               \
    }                                                                          \
  }                                                                            \

#define FourierExtRealOdd3( nsrc, src, srcn, srcinc, dst, dstinc )             \
  {                                                                            \
    Size si = ( srcinc ), di = ( dstinc );                                     \
    const Real *sp = ( src ), *sn = ( srcn );                                  \
    Real *dp = ( dst );                                                        \
    Real *dn = dp + ( nsrc ) * di;                                             \
    if ( dp < dn ) {                                                           \
      *dp = 0; dp += di; sp += si; dn -= di; sn += si;                         \
    }                                                                          \
    while ( dp < dn ) {                                                        \
      *dn = -*sn; dn -= di; sn += si;                                          \
      *dp =  *sp; dp += di; sp += si;                                          \
    }                                                                          \
    if ( dp == dn ) {                                                          \
      *dp = 0;                                                                 \
    }                                                                          \
  }                                                                            \

#define FourierExtCmplxHerm3( nsrc, src, srcn, srcinc, dst, dstinc )           \
  {                                                                            \
    Size si = ( srcinc ), di = ( dstinc );                                     \
    const Cmplx *sp = ( src ), *sn = ( srcn );                                 \
    Cmplx *dp = ( dst );                                                       \
    Cmplx *dn = dp + ( nsrc ) * di;                                            \
    if ( dp < dn ) {                                                           \
      Real re = Re( *sp ); sp += si; sn += si;                                 \
      Cset( *dp, re, 0 ); dp += di; dn -= di;                                  \
    }                                                                          \
    while ( dp < dn ) {                                                        \
      Real re = Re( *sn ), im = Im( *sn ); sn += si;                           \
      Cset( *dn, re, -im ); dn -= di;                                          \
      re = Re( *sp ); im = Im( *sp ); sp += si;                                \
      Cset( *dp, re,  im ); dp += di;                                          \
    }                                                                          \
    if ( dp == dn ) {                                                          \
      Real re = Re( *sp );                                                     \
      Cset( *dp, re, 0 );                                                      \
    }                                                                          \
  }                                                                            \

#define FourierExtCmplxAHerm3( nsrc, src, srcn, srcinc, dst, dstinc )          \
  {                                                                            \
    Size si = ( srcinc ), di = ( dstinc );                                     \
    const Cmplx *sp = ( src ), *sn = ( srcn );                                 \
    Cmplx *dp = ( dst );                                                       \
    Cmplx *dn = dp + ( nsrc ) * di;                                            \
    if ( dp < dn ) {                                                           \
      Real im = Im( *sp ); sp += si; sn += si;                                 \
      Cset( *dp, 0, im ); dp += di; dn -= di;                                  \
    }                                                                          \
    while ( dp < dn ) {                                                        \
      Real re = Re( *sn ), im = Im( *sn ); sn += si;                           \
      Cset( *dn, -re, im ); dn -= di;                                          \
      re = Re( *sp ); im = Im( *sp ); sp += si;                                \
      Cset( *dp,  re, im ); dp += di;                                          \
    }                                                                          \
    if ( dp == dn ) {                                                          \
      Real im = Im( *sp );                                                     \
      Cset( *dp, 0, im );                                                      \
    }                                                                          \
  }                                                                            \

#define FourierUncenterCmplx( ndst, dst )                                      \
  {                                                                            \
    Size nd = ( ndst );                                                        \
    Cmplx *db = ( dst );                                                       \
    if ( nd % 2 ) {                                                            \
      Cmplx *de = db + nd - 1, *d = db + nd / 2;                               \
      Cmplx dt = *de;                                                          \
      while ( d > db ) {                                                       \
        d--; *de = *d; de--; *d = *de;                                         \
      }                                                                        \
      *de = dt;                                                                \
    } else {                                                                   \
      Cmplx *dh = db + nd / 2;                                                 \
      Cmplx *d = db, *de = dh;                                                 \
      while ( d < de ) {                                                       \
        Cmplx dt = *d; *d = *dh; *dh = dt; d++; dh++;                          \
      }                                                                        \
    }                                                                          \
  }                                                                            \

#define FourierUncenterCmplx2( nsrc, src, srcinc, dst, dstinc )                \
  {                                                                            \
    Size ns = ( nsrc ), si = ( srcinc ), di = ( dstinc );                      \
    const Cmplx *sb = ( src ); Cmplx *d = ( dst );                             \
    const Cmplx *se = sb + ns * si, *sh = sb + ( ns / 2 ) * si;                \
    for ( const Cmplx *s = sh; s < se; s += si, d += di ) {                    \
      *d = *s;                                                                 \
    }                                                                          \
    for ( const Cmplx *s = sb; s < sh; s += si, d += di ) {                    \
      *d = *s;                                                                 \
    }                                                                          \
  }                                                                            \


/* prototypes */

extern Status FourierRegister
              (const FourierVersion *vers);

extern void FourierNegative
            (const Fourier *fou,
             Real *dst,
             Size count);

extern void FourierCenterAsymReal
            (Size dim,
             const Size *n,
             const Real *src,
             Real *dst);

extern void FourierCenterSymReal
            (Size dim,
             const Size *n,
             const Real *src,
             Real *dst);

extern void FourierUncenterAsymReal
            (Size dim,
             const Size *n,
             const Real *src,
             Real *dst);

extern void FourierUncenterSymReal
            (Size dim,
             const Size *n,
             const Real *src,
             Real *dst);

extern void FourierCenterAsymCmplx
            (Size dim,
             const Size *n,
             const Cmplx *src,
             Cmplx *dst);

extern void FourierCenterSymCmplx
            (Size dim,
             const Size *n,
             const Cmplx *src,
             Cmplx *dst);

extern void FourierUncenterAsymCmplx
            (Size dim,
             const Size *n,
             const Cmplx *src,
             Cmplx *dst);

extern void FourierUncenterSymCmplx
            (Size dim,
             const Size *n,
             const Cmplx *src,
             Cmplx *dst);

#endif
