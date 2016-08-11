/*----------------------------------------------------------------------------*
*
*  arrayfncutpaste.c  -  array: array operations
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

static Status ArrayFnCutPasteSub
              (Size dim,
               const Size *srclen,
               Offset srcoffs,
               Offset srcsize,
               Size srcelsize,
               void *srcbuf,
               const Size *boxori,
               const Size *boxlen,
               const Size *boxpos,
               const Size *dstlen,
               Offset dstoffs,
               Offset dstsize,
               Size dstelsize,
               void *dstbuf,
               ArraySrcFn srcfn,
               ArrayCpyFn cpyfn,
               ArrayDstFn dstfn,
               void *data)

{
  Size slen, sori;
  Size dlen, dori;
  Size blen, clen, elen;
  Offset soffs, doffs;
  Status status;

  slen = srclen[dim];
  if ( slen == 0 ) return E_NONE;
  srcsize /= slen;
  sori = ( boxori == NULL ) ? 0 : boxori[dim] % slen;
  soffs = srcoffs + sori * srcsize * srcelsize;

  blen = boxlen[dim];
  dlen = dstlen[dim];
  if ( blen > dlen ) blen = dlen;
  if ( blen == 0 ) return E_NONE;
  dstsize /= dlen;
  dori = ( boxpos == NULL ) ? 0 : boxpos[dim] % dlen;
  doffs = dstoffs + dori * dstsize * dstelsize;

  if ( dim ) {

    while ( blen-- ) {

      if ( sori == slen ) {
        soffs = srcoffs;
        sori = 0;
      }
      if ( dori == dlen ) {
        doffs = dstoffs;
        dori = 0;
      }

      status = ArrayFnCutPasteSub( dim - 1, srclen, soffs, srcsize, srcelsize, srcbuf, boxori, boxlen, boxpos, dstlen, doffs, dstsize, dstelsize, dstbuf, srcfn, cpyfn, dstfn, data );
      if ( status ) return status;

      soffs += srcsize * srcelsize;
      sori++;
      doffs += dstsize * dstelsize;
      dori++;

    }

  } else {

    while ( blen > 0 ) {

      clen = slen - sori;
      if ( clen > blen ) clen = blen;

      elen = dlen - dori;
      if ( clen > elen ) clen = elen;

      if ( cpyfn == NULL ) {
        status = srcfn( soffs, clen, srcelsize, dstbuf, data );
        if ( status ) return status;
      } else {
        status = srcfn( soffs, clen, srcelsize, srcbuf, data );
        if ( status ) return status;
        status = cpyfn( clen, srcelsize, srcbuf, dstelsize, dstbuf, data );
        if ( status ) return status;
      }
      status = dstfn( doffs, clen, dstelsize, dstbuf, data );
      if ( status ) return status;

      sori += clen;
      if ( sori == slen ) {
        soffs = srcoffs;
        sori = 0;
      } else {
        soffs += clen * srcelsize;
      }

      dori += clen;
      if ( dori == dlen ) {
        doffs = dstoffs;
        dori = 0;
      } else {
        doffs += clen * dstelsize;
      }

      blen -= clen;

    }

  }

  return status;

}


extern Status ArrayFnCutPaste
              (Size dim,
               const Size *srclen,
               const Size *boxori,
               const Size *boxlen,
               const Size *boxpos,
               const Size *dstlen,
               Size srcelsize,
               Size dstelsize,
               ArraySrcFn srcfn,
               ArrayCpyFn cpyfn,
               ArrayDstFn dstfn,
               void *data)

{
  Offset srcsize, boxsize, dstsize;
  void *dstbuf, *srcbuf = NULL;
  Status status;

  if ( srclen == NULL ) return exception( E_ARGVAL );
  if ( dstlen == NULL ) return exception( E_ARGVAL );
  if ( srcelsize == 0 ) return exception( E_ARGVAL );
  if ( dstelsize == 0 ) return exception( E_ARGVAL );
  if ( srcfn  == NULL ) return exception( E_ARGVAL );
  if ( dstfn  == NULL ) return exception( E_ARGVAL );
  if ( ( cpyfn == NULL ) && ( srcelsize != dstelsize ) )  return exception( E_ARGVAL );

  if ( boxlen  == NULL ) boxlen = srclen;

  status = ArrayOffset( dim, srclen, srcelsize, &srcsize );
  if ( status ) return exception( status );

  status = ArrayFnBox( dim, srclen, boxori, boxlen, srcelsize, NULL, &boxsize );
  if ( status ) return exception( status );

  status = ArrayFnBox( dim, dstlen, boxpos, boxlen, dstelsize, NULL, &boxsize );
  if ( status ) return exception( status );

  status = ArrayOffset( dim, dstlen, dstelsize, &dstsize );
  if ( status ) return exception( status );

  if ( boxsize && dstsize ) {

    dstbuf = malloc( boxlen[0] * dstelsize );
    if ( dstbuf == NULL ) return exception( E_MALLOC );

    if ( cpyfn != NULL ) {
      srcbuf = malloc( srclen[0] * srcelsize );
      if ( srcbuf == NULL ) {
        free( dstbuf );
        return exception( E_MALLOC );
      }
    }

    status = ArrayFnCutPasteSub( dim - 1, srclen, 0, srcsize, srcelsize, srcbuf, boxori, boxlen, boxpos, dstlen, 0, dstsize, dstelsize, dstbuf, srcfn, cpyfn, dstfn, data );
    logexception( status );

    if ( srcbuf != NULL ) free( srcbuf );
    free( dstbuf );

  }

  return status;

}


extern Status ArrayFnCutPasteClip
              (Size dim,
               const Size *srclen,
               const Size *boxori,
               const Size *boxlen,
               const Size *boxpos,
               const Size *dstlen,
               Size srcelsize,
               Size dstelsize,
               ArraySrcFn srcfn,
               ArrayCpyFn cpyfn,
               ArrayDstFn dstfn,
               Size *cutlen,
               void *data)

{
  Offset srcsize, boxsize, dstsize;
  void *dstbuf, *srcbuf = NULL;
  Status status;

  if ( srclen == NULL ) return exception( E_ARGVAL );
  if ( dstlen == NULL ) return exception( E_ARGVAL );
  if ( srcelsize == 0 ) return exception( E_ARGVAL );
  if ( dstelsize == 0 ) return exception( E_ARGVAL );
  if ( srcfn  == NULL ) return exception( E_ARGVAL );
  if ( dstfn  == NULL ) return exception( E_ARGVAL );
  if ( ( cpyfn == NULL ) && ( srcelsize != dstelsize ) )  return exception( E_ARGVAL );
  if ( cutlen == NULL ) return exception( E_ARGVAL );

  if ( boxlen  == NULL ) boxlen = srclen;

  status = ArrayOffset( dim, srclen, srcelsize, &srcsize );
  if ( status ) return exception( status );

  status = ArrayFnBox( dim, srclen, boxori, boxlen, srcelsize, cutlen, &boxsize );
  if ( status ) return exception( status );

  status = ArrayFnBox( dim, dstlen, boxpos, cutlen, dstelsize, cutlen, &boxsize );
  if ( status ) return exception( status );

  status = ArrayOffset( dim, dstlen, dstelsize, &dstsize );
  if ( status ) return exception( status );

  if ( boxsize && dstsize ) {

    dstbuf = malloc( boxlen[0] * dstelsize );
    if ( dstbuf == NULL ) return exception( E_MALLOC );

    if ( cpyfn != NULL ) {
      srcbuf = malloc( srclen[0] * srcelsize );
      if ( srcbuf == NULL ) {
        free( dstbuf );
        return exception( E_MALLOC );
      }
    }

    status = ArrayFnCutPasteSub( dim - 1, srclen, 0, srcsize, srcelsize, srcbuf, boxori, boxlen, boxpos, dstlen, 0, dstsize, dstelsize, dstbuf, srcfn, cpyfn, dstfn, data );
    logexception( status );

    if ( srcbuf != NULL ) free( srcbuf );
    free( dstbuf );

  }

  return status;

}


extern Status ArrayFnCutPasteCyc
              (Size dim,
               const Size *srclen,
               const Size *boxori,
               const Size *boxlen,
               const Size *boxpos,
               const Size *dstlen,
               Size srcelsize,
               Size dstelsize,
               ArraySrcFn srcfn,
               ArrayCpyFn cpyfn,
               ArrayDstFn dstfn,
               void *data)

{
  Offset srcsize, boxsize, dstsize;
  void *dstbuf, *srcbuf = NULL;
  Status status;

  if ( srclen == NULL ) return exception( E_ARGVAL );
  if ( dstlen == NULL ) return exception( E_ARGVAL );
  if ( srcelsize == 0 ) return exception( E_ARGVAL );
  if ( dstelsize == 0 ) return exception( E_ARGVAL );
  if ( srcfn  == NULL ) return exception( E_ARGVAL );
  if ( dstfn  == NULL ) return exception( E_ARGVAL );
  if ( ( cpyfn == NULL ) && ( srcelsize != dstelsize ) )  return exception( E_ARGVAL );

  if ( boxlen  == NULL ) boxlen = srclen;

  status = ArrayOffset( dim, srclen, srcelsize, &srcsize );
  if ( status ) return exception( status );

  status = ArrayOffset( dim, boxlen, srcelsize, &boxsize );
  if ( status ) return exception( status );

  status = ArrayOffset( dim, dstlen, dstelsize, &dstsize );
  if ( status ) return exception( status );

  if ( boxsize && dstsize ) {

    dstbuf = malloc( boxlen[0] * dstelsize );
    if ( dstbuf == NULL ) return exception( E_MALLOC );

    if ( cpyfn != NULL ) {
      srcbuf = malloc( srclen[0] * srcelsize );
      if ( srcbuf == NULL ) {
        free( dstbuf );
        return exception( E_MALLOC );
      }
    }

    status = ArrayFnCutPasteSub( dim - 1, srclen, 0, srcsize, srcelsize, srcbuf, boxori, boxlen, boxpos, dstlen, 0, dstsize, dstelsize, dstbuf, srcfn, cpyfn, dstfn, data );
    logexception( status );

    if ( srcbuf != NULL ) free( srcbuf );
    free( dstbuf );

  }

  return status;

}
