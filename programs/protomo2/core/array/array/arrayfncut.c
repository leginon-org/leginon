/*----------------------------------------------------------------------------*
*
*  arrayfncut.c  -  array: array operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "array.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* functions */

static Status ArrayFnCutSub
              (Size dim,
               const Size *srclen,
               Offset srcoffs,
               Offset srcsize,
               Size srcelsize,
               void *srcbuf,
               const Size *boxori,
               const Size *boxlen,
               Offset *dstoffs,
               Size dstelsize,
               void *dstbuf,
               ArraySrcFn srcfn,
               ArrayCpyFn cpyfn,
               ArrayDstFn dstfn,
               void *data)

{
  Size slen, sori;
  Size dlen, clen;
  Offset soffs;
  Size dstlen = 0;
  char *dbuf = dstbuf;
  Status status;

  slen = srclen[dim];
  if ( slen == 0 ) return E_NONE;
  srcsize /= slen;
  sori = ( boxori == NULL ) ? 0 : boxori[dim] % slen;
  soffs = srcoffs + sori * srcsize * srcelsize;

  dlen = boxlen[dim];

  if ( dim ) {

    while ( dlen-- ) {

      if ( sori == slen ) {
        soffs = srcoffs;
        sori = 0;
      }

      status = ArrayFnCutSub( dim - 1, srclen, soffs, srcsize, srcelsize, srcbuf, boxori, boxlen, dstoffs, dstelsize, dstbuf, srcfn, cpyfn, dstfn, data );
      if ( status ) return status;

      soffs += srcsize * srcelsize;
      sori++;

    }

  } else {

    clen = slen - sori;

    while ( dlen > 0 ) {

      if ( clen > dlen ) clen = dlen;

      if ( cpyfn == NULL ) {
        status = srcfn( soffs, clen, srcelsize, dbuf, data );
        if ( status ) return status;
      } else {
        status = srcfn( soffs, clen, srcelsize, srcbuf, data );
        if ( status ) return status;
        status = cpyfn( clen, srcelsize, srcbuf, dstelsize, dbuf, data );
        if ( status ) return status;
      }

      dlen -= clen;
      dstlen += clen;
      dbuf += clen * dstelsize;

      soffs = srcoffs;
      clen = slen;

    }

    if ( dstlen ) {
     status = dstfn( *dstoffs, dstlen, dstelsize, dstbuf, data );
     if ( status ) return status;
     *dstoffs += dstlen * dstelsize;
    }

  }

  return E_NONE;

}


extern Status ArrayFnCut
              (Size dim,
               const Size *srclen,
               const Size *boxori,
               const Size *boxlen,
               Size srcelsize,
               Size dstelsize,
               ArraySrcFn srcfn,
               ArrayCpyFn cpyfn,
               ArrayDstFn dstfn,
               void *data)

{
  Offset srcsize, boxsize;
  Offset dstoffs = 0;
  void *dstbuf, *srcbuf = NULL;
  Status status;

  if ( srclen == NULL ) return exception( E_ARGVAL );
  if ( boxlen == NULL ) return exception( E_ARGVAL );
  if ( srcelsize == 0 ) return exception( E_ARGVAL );
  if ( dstelsize == 0 ) return exception( E_ARGVAL );
  if ( srcfn  == NULL ) return exception( E_ARGVAL );
  if ( dstfn  == NULL ) return exception( E_ARGVAL );
  if ( ( cpyfn == NULL ) && ( srcelsize != dstelsize ) )  return exception( E_ARGVAL );

  status = ArrayOffset( dim, srclen, srcelsize, &srcsize );
  if ( status ) return exception( status );

  status = ArrayFnBox( dim, srclen, boxori, boxlen, dstelsize, NULL, &boxsize );
  if ( status ) return exception( status );

  if ( boxsize ) {

    dstbuf = malloc( boxlen[0] * dstelsize );
    if ( dstbuf == NULL ) return exception( E_MALLOC );

    if ( cpyfn != NULL ) {
      srcbuf = malloc( srclen[0] * srcelsize );
      if ( srcbuf == NULL ) {
        free( dstbuf );
        return exception( E_MALLOC );
      }
    }

    status = ArrayFnCutSub( dim - 1, srclen, 0, srcsize, srcelsize, srcbuf, boxori, boxlen, &dstoffs, dstelsize, dstbuf, srcfn, cpyfn, dstfn, data );
    logexception( status );

    if ( srcbuf != NULL ) free( srcbuf );
    free( dstbuf );

  }

  return status;

}


extern Status ArrayFnCutClip
              (Size dim,
               const Size *srclen,
               const Size *boxori,
               const Size *boxlen,
               Size *dstlen,
               Size srcelsize,
               Size dstelsize,
               ArraySrcFn srcfn,
               ArrayCpyFn cpyfn,
               ArrayDstFn dstfn,
               void *data)

{
  Offset srcsize, boxsize;
  Offset dstoffs = 0;
  void *dstbuf, *srcbuf = NULL;
  Status status;

  if ( srclen == NULL ) return exception( E_ARGVAL );
  if ( boxlen == NULL ) return exception( E_ARGVAL );
  if ( dstlen == NULL ) return exception( E_ARGVAL );
  if ( srcelsize == 0 ) return exception( E_ARGVAL );
  if ( dstelsize == 0 ) return exception( E_ARGVAL );
  if ( srcfn  == NULL ) return exception( E_ARGVAL );
  if ( dstfn  == NULL ) return exception( E_ARGVAL );
  if ( ( cpyfn == NULL ) && ( srcelsize != dstelsize ) )  return exception( E_ARGVAL );

  status = ArrayOffset( dim, srclen, srcelsize, &srcsize );
  if ( status ) return exception( status );

  status = ArrayFnBox( dim, srclen, boxori, boxlen, dstelsize, dstlen, &boxsize );
  if ( status && ( status != E_ARRAY_BOUNDS ) ) return exception( status );

  if ( boxsize ) {

    dstbuf = malloc( boxlen[0] * dstelsize );
    if ( dstbuf == NULL ) return exception( E_MALLOC );

    if ( cpyfn != NULL ) {
      srcbuf = malloc( srclen[0] * srcelsize );
      if ( srcbuf == NULL ) {
        free( dstbuf );
        return exception( E_MALLOC );
      }
    }

    status = ArrayFnCutSub( dim - 1, srclen, 0, srcsize, srcelsize, srcbuf, boxori, boxlen, &dstoffs, dstelsize, dstbuf, srcfn, cpyfn, dstfn, data );
    logexception( status );

    if ( srcbuf != NULL ) free( srcbuf );
    free( dstbuf );

  }

  return status;

}


extern Status ArrayFnCutCyc
              (Size dim,
               const Size *srclen,
               const Size *boxori,
               const Size *boxlen,
               Size srcelsize,
               Size dstelsize,
               ArraySrcFn srcfn,
               ArrayCpyFn cpyfn,
               ArrayDstFn dstfn,
               void *data)

{
  Offset srcsize, boxsize;
  Offset dstoffs = 0;
  void *dstbuf, *srcbuf = NULL;
  Status status;

  if ( srclen == NULL ) return exception( E_ARGVAL );
  if ( boxlen == NULL ) return exception( E_ARGVAL );
  if ( srcelsize == 0 ) return exception( E_ARGVAL );
  if ( dstelsize == 0 ) return exception( E_ARGVAL );
  if ( srcfn  == NULL ) return exception( E_ARGVAL );
  if ( dstfn  == NULL ) return exception( E_ARGVAL );
  if ( ( cpyfn == NULL ) && ( srcelsize != dstelsize ) )  return exception( E_ARGVAL );

  status = ArrayOffset( dim, srclen, srcelsize, &srcsize );
  if ( status ) return exception( status );

  status = ArrayOffset( dim, srclen, srcelsize, &boxsize );
  if ( status ) return exception( status );

  if ( boxsize ) {

    dstbuf = malloc( boxlen[0] * dstelsize );
    if ( dstbuf == NULL ) return exception( E_MALLOC );

    if ( cpyfn != NULL ) {
      srcbuf = malloc( srclen[0] * srcelsize );
      if ( srcbuf == NULL ) {
        free( dstbuf );
        return exception( E_MALLOC );
      }
    }

    status = ArrayFnCutSub( dim - 1, srclen, 0, srcsize, srcelsize, srcbuf, boxori, boxlen, &dstoffs, dstelsize, dstbuf, srcfn, cpyfn, dstfn, data );
    logexception( status );

    if ( srcbuf != NULL ) free( srcbuf );
    free( dstbuf );

  }

  return status;

}
