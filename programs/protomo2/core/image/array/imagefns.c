/*----------------------------------------------------------------------------*
*
*  imagefns.c  -  image: array operations
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
  nrfields
};


/* functions */

static Status ImageFnSub
              (ImageFn fns,
               const Type type,
               const void *srcpos,
               const void *srcneg,
               void *dst,
               Size dim,
               const Size *par)

{
  Status status;

  Size slen = par[srclen];

  if ( dim-- ) {

    const char *spaddr = srcpos, *snaddr = srcneg;

    Size sp = par[srcori], sn = sp;
    Size sinc = par[srcinc];

    const char *spa = spaddr + sinc * sp;
    const char *sna = snaddr + sinc * sn;

    par -= nrfields;

    status = ImageFnSub( fns, type, spa, sna, dst, dim, par );
    if ( status ) return status;

    Size i = 1;

    while ( i < ( slen + 1 ) / 2 ) {
      sp++; if ( sp == slen ) sp = 0;
      if ( sn == 0 ) sn = slen; sn--;
      spa = spaddr + sinc * sp;
      sna = snaddr + sinc * sn;
      status = ImageFnSub( fns, type, spa, sna, dst, dim, par );
      if ( status ) return status;
      i++;
    }

    if ( !( slen % 2 ) ) {
      sp++; if ( sp == slen ) sp = 0;
      if ( sn == 0 ) sn = slen; sn--;
      spa = spaddr + sinc * sp;
      sna = snaddr + sinc * sn;
      status = ImageFnSub( fns, type, spa, sna, dst, dim, par );
      if ( status ) return status;
      i++;
    }

    while ( i < slen ) {
      sp++; if ( sp == slen ) sp = 0;
      if ( sn == 0 ) sn = slen; sn--;
      spa = spaddr + sinc * sp;
      sna = snaddr + sinc * sn;
      status = ImageFnSub( fns, type, spa, sna, dst, dim, par );
      if ( status ) return status;
      i++;
    }

  } else {

    status = fns( type, slen, srcpos, srcneg, par[dstlen], dst );
    if ( status ) return status;

  }

  return E_NONE;

}


static Status ImageFnsSym
              (ImageFn fns,
               const Image *src,
               const void *srcaddr,
               void *dstaddr)

{
  Status status;

  if ( argcheck( fns == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstaddr == NULL ) ) return exception( E_ARGVAL );

  if ( runcheck && !( src->attr & ImageSymMask ) ) return exception( E_IMAGEARRAY );

  Size dim = src->dim;
  if ( !dim ) return exception( E_ARRAY_ZERO );

  Size *param = malloc( nrfields * dim * sizeof(Size) );
  if ( param == NULL ) return exception( E_MALLOC );

  Image dst;
  dst.low = NULL;
  dst.len = param;
  status = ImageMetaCopy( src, &dst, ImageModeSym );
  if ( exception( status ) ) goto exit;

  Size *par = param;
  par[dstlen] = dst.len[0];
  Size slen = par[srclen] = src->len[0];
  Size sinc = par[srcinc] = TypeGetSize( src->type );
  par[srcori] = 0;
  for ( Size d = 1; d < dim; d++ ) {
    par += nrfields;
    sinc *= slen; par[srcinc] = sinc; slen = par[srclen] = src->len[d];
    if ( slen == 0 ) { status = exception( E_ARRAY_ZERO ); goto exit; }
    Index slow = src->low[d];
    if ( slow > 0 ) {
      par[srcori] = slen - slow % slen;
      if ( par[srcori] == slen ) par[srcori] = 0;
    } else {
      par[srcori] = ( -slow ) % slen;
    }
  }

  status = ImageFnSub( fns, src->type, srcaddr, srcaddr, dstaddr, dim - 1, par );
  logexception( status );

  exit:
  free( param );

  return status;

}


extern Status ImageFnsAsym
              (ImageFn fns,
               const Image *src,
               const void *srcaddr,
               void *dstaddr)

{
  Status status;

  if ( argcheck( fns == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstaddr == NULL ) ) return exception( E_ARGVAL );

  if ( runcheck && ( src->attr & ImageSymMask ) ) return exception( E_IMAGEARRAY );

  Size srclen;
  status = ArraySize( src->dim, src->len, TypeGetSize( src->type ), &srclen );
  if ( exception( status ) ) return status;
  if ( !srclen ) return exception( E_ARRAY_ZERO );

  status = fns( src->type, srclen, srcaddr, srcaddr, srclen, dstaddr );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern Status ImageFnsEven
              (ImageFn fns,
               const Image *src,
               const void *srcaddr,
               void *dstaddr)

{
  Status status;

  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );

  if ( ( src->attr & ImageSymMask ) != ImageSymEven ) return exception( E_ARGVAL );

  status = ImageFnsSym( fns, src, srcaddr, dstaddr );
  logexception( status );

  return status;

}


extern Status ImageFnsOdd
              (ImageFn fns,
               const Image *src,
               const void *srcaddr,
               void *dstaddr)

{
  Status status;

  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );

  if ( ( src->attr & ImageSymMask ) != ImageSymOdd ) return exception( E_ARGVAL );

  status = ImageFnsSym( fns, src, srcaddr, dstaddr );
  logexception( status );

  return status;

}


extern Status ImageFnsHerm
              (ImageFn fns,
               const Image *src,
               const void *srcaddr,
               void *dstaddr)

{
  Status status;

  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );

  if ( ( src->attr & ImageSymMask ) != ImageSymHerm ) return exception( E_ARGVAL );

  status = ImageFnsSym( fns, src, srcaddr, dstaddr );
  logexception( status );

  return status;

}


extern Status ImageFnsAHerm
              (ImageFn fns,
               const Image *src,
               const void *srcaddr,
               void *dstaddr)

{
  Status status;

  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );

  if ( ( src->attr & ImageSymMask ) != ImageSymAHerm ) return exception( E_ARGVAL );

  status = ImageFnsSym( fns, src, srcaddr, dstaddr );
  logexception( status );

  return status;

}


extern Status ImageFnsExec
              (const ImageFnTab *fns,
               const Image *src,
               const void *srcaddr,
               void *dstaddr)

{
  Status status;

  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstaddr == NULL ) ) return exception( E_ARGVAL );

  switch ( src->attr & ImageSymMask ) {
    case ImageAsym:     status = exception( ImageFnsAsym( fns->asym,  src, srcaddr, dstaddr ) ); break;
    case ImageSymEven:  status = exception( ImageFnsSym ( fns->even,  src, srcaddr, dstaddr ) ); break;
    case ImageSymOdd:   status = exception( ImageFnsSym ( fns->odd,   src, srcaddr, dstaddr ) ); break;
    case ImageSymHerm:  status = exception( ImageFnsSym ( fns->herm,  src, srcaddr, dstaddr ) ); break;
    case ImageSymAHerm: status = exception( ImageFnsSym ( fns->aherm, src, srcaddr, dstaddr ) ); break;
    default: status = exception( E_IMAGEARRAY );
  }

  return status;

}
