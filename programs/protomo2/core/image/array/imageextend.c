/*----------------------------------------------------------------------------*
*
*  imageextend.c  -  image: array operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagearray.h"
#include "exception.h"
#include "mathdefs.h"
#include <stdlib.h>


/* types */

typedef Status (*ImageExtendFn)(Type, Size, const void *, const void *, Size, Size, void *);

enum {
  srclen,
  srcori,
  srcinc,
  dstlen,
  dstori,
  dstinc,
  nrfields
};


/* macros */

#define PosReal( src, dst )                                                  \
  {                                                                          \
    Real s = src, *d = dst;                                                  \
    *d = s;                                                                  \
  }                                                                          \

#define PosCmplx( src, dst )                                                 \
  {                                                                          \
    Cmplx s = src, *d = dst;                                                 \
    *d = s;                                                                  \
  }                                                                          \

#define NegReal( src, dst )                                                  \
  {                                                                          \
    Real s = src, *d = dst;                                                  \
    *d = -s;                                                                 \
  }                                                                          \

#define NegCmplx( src, dst )                                                 \
  {                                                                          \
    Cmplx s = src, *d = dst;                                                 \
    Cset( *d, -Re( s ), -Im( s ) );                                          \
  }                                                                          \

#define Herm( src, dst )                                                     \
  {                                                                          \
    Cmplx s = src, *d = dst;                                                 \
    Cset( *d, Re( s ), -Im( s ) );                                           \
  }                                                                          \

#define AHerm( src, dst )                                                    \
  {                                                                          \
    Cmplx s = src, *d = dst;                                                 \
    Cset( *d, -Re( s ), Im( s ) );                                           \
  }                                                                          \

#define Extend( type, symassign )                                            \
  {                                                                          \
    const type *sp = srcpos, *sn = srcneg, *se = sp + ( dstlen + 1 ) / 2;    \
    type *dp = dst, *de = dp + dstlen; dp += dstori;                         \
    type *dn = dp;                                                           \
    *dp++ = *sp++; if ( dp == de ) dp = dst;                                 \
    sn++; if ( dn == dst ) dn += dstlen; dn--;                               \
    while ( sp < se ) {                                                      \
      *dp++ = *sp++; if ( dp == de ) dp = dst;                               \
      symassign( *sn++, dn ); if ( dn == dst ) dn += dstlen; dn--;           \
    }                                                                        \
    se = srcpos; se += srclen;                                               \
    if ( sp < se ) {                                                         \
      *dp = *sp;                                                             \
    }                                                                        \
  }                                                                          \


/* functions */

static Status ImageExtendSymEven
              (Type type,
               Size srclen,
               const void *srcpos,
               const void *srcneg,
               Size dstlen,
               Size dstori,
               void *dst)

{

  switch ( type ) {
    case TypeReal:
    case TypeImag:  Extend( Real,  PosReal  ); break;
    case TypeCmplx: Extend( Cmplx, PosCmplx ); break;
    default: return exception( E_IMAGE_TYPE );
  }

  return E_NONE;

}


static Status ImageExtendSymOdd
              (Type type,
               Size srclen,
               const void *srcpos,
               const void *srcneg,
               Size dstlen,
               Size dstori,
               void *dst)

{

  switch ( type ) {
    case TypeReal:
    case TypeImag:  Extend( Real,  NegReal  ); break;
    case TypeCmplx: Extend( Cmplx, NegCmplx ); break;
    default: return exception( E_IMAGE_TYPE );
  }

  return E_NONE;

}


static Status ImageExtendSymHerm
              (Type type,
               Size srclen,
               const void *srcpos,
               const void *srcneg,
               Size dstlen,
               Size dstori,
               void *dst)

{

  switch ( type ) {
    case TypeReal:  Extend( Real, PosReal ); break;
    case TypeImag:  Extend( Real, NegReal ); break;
    case TypeCmplx: Extend( Cmplx,   Herm ); break;
    default: return exception( E_IMAGE_TYPE );
  }

  return E_NONE;

}


static Status ImageExtendSymAHerm
              (Type type,
               Size srclen,
               const void *srcpos,
               const void *srcneg,
               Size dstlen,
               Size dstori,
               void *dst)

{

  switch ( type ) {
    case TypeReal:  Extend( Real, NegReal ); break;
    case TypeImag:  Extend( Real, PosReal ); break;
    case TypeCmplx: Extend( Cmplx,  AHerm ); break;
    default: return exception( E_IMAGE_TYPE );
  }

  return E_NONE;

}


static Status ImageExtendSub
              (ImageExtendFn extend,
               const Type type,
               const void *srcpos,
               const void *srcneg,
               void *dst,
               Size dim,
               const Size *par)

{
  Status status;

  Size slen = par[srclen];
  Size dlen = par[dstlen];
  Size d = par[dstori];

  if ( dim-- ) {

    const char *spaddr = srcpos, *snaddr = srcneg;
    char *daddr = dst;

    Size sp = par[srcori], sn = sp;
    Size sinc = par[srcinc];
    Size dinc = par[dstinc];

    const char *spa = spaddr + sinc * sp;
    const char *sna = snaddr + sinc * sn;
    char *da = daddr + dinc * d;

    par -= nrfields;

    status = ImageExtendSub( extend, type, spa, sna, da, dim, par );
    if ( status ) return status;

    Size i = 1;

    while ( i < ( slen + 1 ) / 2 ) {
      sp++; if ( sp == slen ) sp = 0;
      if ( sn == 0 ) sn = slen; sn--;
      d++; if ( d == dlen ) d = 0;
      spa = spaddr + sinc * sp;
      sna = snaddr + sinc * sn;
      da = daddr + dinc * d;
      status = ImageExtendSub( extend, type, spa, sna, da, dim, par );
      if ( status ) return status;
      i++;
    }

    if ( !( slen % 2 ) ) {
      sp++; if ( sp == slen ) sp = 0;
      if ( sn == 0 ) sn = slen; sn--;
      d++; if ( d == dlen ) d = 0;
      spa = spaddr + sinc * sp;
      sna = snaddr + sinc * sn;
      da = daddr + dinc * d;
      status = ImageExtendSub( extend, type, spa, sna, da, dim, par );
      if ( status ) return status;
      i++;
    }

    while ( i < slen ) {
      sp++; if ( sp == slen ) sp = 0;
      if ( sn == 0 ) sn = slen; sn--;
      d++; if ( d == dlen ) d = 0;
      spa = spaddr + sinc * sp;
      sna = snaddr + sinc * sn;
      da = daddr + dinc * d;
      status = ImageExtendSub( extend, type, spa, sna, da, dim, par );
      if ( status ) return status;
      i++;
    }

  } else {

    status = extend( type, slen, srcpos, srcneg, dlen, d, dst );
    if ( status ) return status;

  }

  return E_NONE;

}


static Status ImageExtendSym
              (ImageExtendFn extend,
               const Image *src,
               const void *srcaddr,
               const Image *dst,
               void *dstaddr,
               ImageMode mode)

{
  Status status;

  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dst == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( extend == NULL ) ) return exception( E_ARGVAL );

  if ( runcheck && ( src->dim != dst->dim ) ) return exception( E_IMAGEARRAY );
  if ( runcheck && ( src->type != dst->type ) ) return exception( E_IMAGEARRAY );
  if ( runcheck && ( dst->attr & ImageSymMask ) ) return exception( E_IMAGEARRAY );

  if ( src->low[0] ) return exception( E_IMAGE_SYM );
  if ( src->len[0] != dst->len[0] / 2 + 1 ) return exception( E_IMAGEARRAY_SYMSIZE );

  Size dim = src->dim;
  if ( !dim ) return exception( E_ARRAY_ZERO );

  Size *param = malloc( nrfields * dim * sizeof(Size) );
  if ( param == NULL ) return exception( E_MALLOC );

  Size *par = param;
  Size slen = par[srclen] = src->len[0];
  Size sinc = par[srcinc] = TypeGetSize( src->type );
  par[srcori] = 0;
  Size dlen = par[dstlen] = dst->len[0];
  Size dinc = par[dstinc] = TypeGetSize( src->type );
  for ( Size d = 1; d < dim; d++ ) {
    par += nrfields;
    sinc *= slen; par[srcinc] = sinc; slen = par[srclen] = src->len[d];
    dinc *= dlen; par[dstinc] = dinc; dlen = par[dstlen] = dst->len[d];
    if ( slen == 0 ) { status = exception( E_ARRAY_ZERO ); goto exit; }
    if ( slen != dlen ) { status = exception( E_IMAGEARRAY_SYMSIZE ); goto exit; }
    Index slow = src->low[d];
    if ( slow > 0 ) {
      par[srcori] = slen - slow % slen;
      if ( par[srcori] == slen ) par[srcori] = 0;
    } else {
      par[srcori] = ( -slow ) % slen;
    }
  }

  par = param;
  for ( Size d = 0; d < dim; d++ ) {
    Size dlen = dst->len[d];
    Index dlow;
    if ( dst->low == NULL ) {
      if ( mode & ImageModeZero ) {
        dlow = 0;
      } else if ( ( mode & ImageModeCtr ) || ( dst->attr & ImageFourspc ) ) {
        dlow = -(Index)( dlen / 2 );
      } else {
        dlow = 0;
      }
    } else {
      dlow = dst->low[d];
    }
    if ( dlow > 0 ) {
      par[dstori] = dlen - dlow % dlen;
      if ( par[dstori] == dlen ) par[dstori] = 0;
    } else {
      par[dstori] = ( -dlow ) % dlen;
    }
    par += nrfields;
  }

  status = ImageExtendSub( extend, src->type, srcaddr, srcaddr, dstaddr, dim - 1, par - nrfields );
  logexception( status );

  exit:
  free( param );

  return status;

}


extern Status ImageExtend
              (const Image *src,
               const void *srcaddr,
               const Image *dst,
               void *dstaddr,
               ImageMode mode)

{
  Status status;

  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstaddr == NULL ) ) return exception( E_ARGVAL );

  mode &= ImageModeZero | ImageModeCtr;
  if ( mode == ( ImageModeZero | ImageModeCtr ) ) {
    return exception( E_ARGVAL );
  }

  switch ( src->attr & ImageSymMask ) {
    case ImageAsym:     status = exception( E_IMAGEARRAY_ASYM );
    case ImageSymEven:  status = exception( ImageExtendSym( ImageExtendSymEven,  src, srcaddr, dst, dstaddr, mode ) ); break;
    case ImageSymOdd:   status = exception( ImageExtendSym( ImageExtendSymOdd,   src, srcaddr, dst, dstaddr, mode ) ); break;
    case ImageSymHerm:  status = exception( ImageExtendSym( ImageExtendSymHerm,  src, srcaddr, dst, dstaddr, mode ) ); break;
    case ImageSymAHerm: status = exception( ImageExtendSym( ImageExtendSymAHerm, src, srcaddr, dst, dstaddr, mode ) ); break;
    default: status = exception( E_IMAGEARRAY );
  }

  return status;

}
