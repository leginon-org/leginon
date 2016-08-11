/*----------------------------------------------------------------------------*
*
*  imagefn.c  -  image: array operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagearraycommon.h"
#include "exception.h"
#include "mathdefs.h"
#include <stdlib.h>


/* types */

enum {
  srclen,
  srcori,
  srcinc,
  dstlen,
  dstinc,
  nrfields
};


/* functions */

static Status ImageFnSub
              (ImageFn fn,
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

  if ( dim-- ) {

    const char *spaddr = srcpos, *snaddr = srcneg;
    char *daddr = dst;

    Size sp = par[srcori], sn = sp;
    Size sinc = par[srcinc];
    Size dinc = par[dstinc];

    const char *spa = spaddr + sinc * sp;
    const char *sna = snaddr + sinc * sn;
    char *da = daddr;

    par -= nrfields;

    status = ImageFnSub( fn, type, spa, sna, da, dim, par );
    if ( status ) return status;

    Size i = 1;

    while ( i < ( slen + 1 ) / 2 ) {
      sp++; if ( sp == slen ) sp = 0;
      if ( sn == 0 ) sn = slen; sn--;
      spa = spaddr + sinc * sp;
      sna = snaddr + sinc * sn;
      da += dinc;
      status = ImageFnSub( fn, type, spa, sna, da, dim, par );
      if ( status ) return status;
      i++;
    }

    if ( !( slen % 2 ) ) {
      sp++; if ( sp == slen ) sp = 0;
      if ( sn == 0 ) sn = slen; sn--;
      spa = spaddr + sinc * sp;
      sna = snaddr + sinc * sn;
      da += dinc;
      status = ImageFnSub( fn, type, spa, sna, da, dim, par );
      if ( status ) return status;
      i++;
    }

    while ( i < slen ) {
      sp++; if ( sp == slen ) sp = 0;
      if ( sn == 0 ) sn = slen; sn--;
      spa = spaddr + sinc * sp;
      sna = snaddr + sinc * sn;
      da += dinc;
      status = ImageFnSub( fn, type, spa, sna, da, dim, par );
      if ( status ) return status;
      i++;
    }

  } else {

    status = fn( type, slen, srcpos, srcneg, dlen, dst );
    if ( status ) return status;

  }

  return E_NONE;

}


static Status ImageFnSym
              (ImageFn fn,
               const Image *src,
               const void *srcaddr,
               void *dstaddr,
               ImageMode mode)

{
  Status status;

  if ( argcheck( fn == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstaddr == NULL ) ) return exception( E_ARGVAL );

  if ( runcheck && !( src->attr & ImageSymMask ) ) return exception( E_IMAGEARRAY );

  mode &= ImageModeZero | ImageModeCtr;
  if ( mode == ( ImageModeZero | ImageModeCtr ) ) {
    return exception( E_ARGVAL );
  }

  Size dim = src->dim;
  if ( !dim ) return exception( E_ARRAY_ZERO );

  Size *param = malloc( nrfields * dim * sizeof(Size) );
  if ( param == NULL ) return exception( E_MALLOC );

  Image dst;
  dst.len = param;
  dst.low = malloc( dim * sizeof(Index) );
  if ( dst.low == NULL ) { status = exception( E_MALLOC ); goto exit1; }
  status = ImageMetaCopy( src, &dst, mode | ImageModeSym );
  if ( exception( status ) ) goto exit2;

  Size *par = param ;
  for ( Size d = 0; d < dim; d++ ) {
    par[dstlen] = dst.len[d];
    par += nrfields;
  }
  par = param;
  Size slen = par[srclen] = src->len[0];
  Size sinc = par[srcinc] = TypeGetSize( src->type );
  par[srcori] = 0;
  Size dlen = par[dstlen];
  Size dinc = par[dstinc] = TypeGetSize( src->type );
  for ( Size d = 1; d < dim; d++ ) {
    par += nrfields;
    sinc *= slen; par[srcinc] = sinc; slen = par[srclen] = src->len[d];
    dinc *= dlen; par[dstinc] = dinc; dlen = par[dstlen];
    if ( slen == 0 ) { status = exception( E_ARRAY_ZERO ); goto exit2; }
    Index slow = src->low[d];
    if ( slow > 0 ) {
      par[srcori] = slen - slow % slen;
      if ( par[srcori] == slen ) par[srcori] = 0;
    } else {
      par[srcori] = ( -slow ) % slen;
    }
  }

  status = ImageFnSub( fn, src->type, srcaddr, srcaddr, dstaddr, dim - 1, par );
  logexception( status );

  exit1: free( dst.low );
  exit2: free( param );

  return status;

}


extern Status ImageFnAsym
              (ImageFn fn,
               const Image *src,
               const void *srcaddr,
               void *dstaddr,
               ImageMode mode)

{
  Status status;

  if ( argcheck( fn == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstaddr == NULL ) ) return exception( E_ARGVAL );

  if ( runcheck && ( src->attr & ImageSymMask ) ) return exception( E_IMAGEARRAY );

  mode &= ImageModeZero | ImageModeCtr;
  if ( mode == ( ImageModeZero | ImageModeCtr ) ) {
    return exception( E_ARGVAL );
  }

  Size srclen;
  status = ArraySize( src->dim, src->len, TypeGetSize( src->type ), &srclen );
  if ( exception( status ) ) return status;
  if ( !srclen ) return exception( E_ARRAY_ZERO );

  status = fn( src->type, srclen, srcaddr, srcaddr, srclen, dstaddr );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern Status ImageFnEven
              (ImageFn fn,
               const Image *src,
               const void *srcaddr,
               void *dstaddr,
               ImageMode mode)

{
  Status status;

  if ( argcheck( fn == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstaddr == NULL ) ) return exception( E_ARGVAL );

  if ( ( src->attr & ImageSymMask ) != ImageSymEven ) return exception( E_ARGVAL );

  status = ImageFnSym( fn, src, srcaddr, dstaddr, mode );
  logexception( status );

  return status;

}


extern Status ImageFnOdd
              (ImageFn fn,
               const Image *src,
               const void *srcaddr,
               void *dstaddr,
               ImageMode mode)

{
  Status status;

  if ( argcheck( fn == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstaddr == NULL ) ) return exception( E_ARGVAL );

  if ( ( src->attr & ImageSymMask ) != ImageSymOdd ) return exception( E_ARGVAL );

  status = ImageFnSym( fn, src, srcaddr, dstaddr, mode );
  logexception( status );

  return status;

}


extern Status ImageFnHerm
              (ImageFn fn,
               const Image *src,
               const void *srcaddr,
               void *dstaddr,
               ImageMode mode)

{
  Status status;

  if ( argcheck( fn == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstaddr == NULL ) ) return exception( E_ARGVAL );

  if ( ( src->attr & ImageSymMask ) != ImageSymHerm ) return exception( E_ARGVAL );

  status = ImageFnSym( fn, src, srcaddr, dstaddr, mode );
  logexception( status );

  return status;

}


extern Status ImageFnAHerm
              (ImageFn fn,
               const Image *src,
               const void *srcaddr,
               void *dstaddr,
               ImageMode mode)

{
  Status status;

  if ( argcheck( fn == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstaddr == NULL ) ) return exception( E_ARGVAL );

  if ( ( src->attr & ImageSymMask ) != ImageSymAHerm ) return exception( E_ARGVAL );

  status = ImageFnSym( fn, src, srcaddr, dstaddr, mode );
  logexception( status );

  return status;

}


extern Status ImageFnExec
              (const ImageFnTab *fn,
               const Image *src,
               const void *srcaddr,
               void *dstaddr,
               ImageMode mode)

{
  Status status;

  if ( argcheck( fn == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstaddr == NULL ) ) return exception( E_ARGVAL );

  switch ( src->attr & ImageSymMask ) {
    case ImageAsym:     status = exception( ImageFnAsym( fn->asym,  src, srcaddr, dstaddr, mode ) ); break;
    case ImageSymEven:  status = exception( ImageFnSym ( fn->even,  src, srcaddr, dstaddr, mode ) ); break;
    case ImageSymOdd:   status = exception( ImageFnSym ( fn->odd,   src, srcaddr, dstaddr, mode ) ); break;
    case ImageSymHerm:  status = exception( ImageFnSym ( fn->herm,  src, srcaddr, dstaddr, mode ) ); break;
    case ImageSymAHerm: status = exception( ImageFnSym ( fn->aherm, src, srcaddr, dstaddr, mode ) ); break;
    default: status = exception( E_IMAGEARRAY );
  }

  return status;

}
