/*----------------------------------------------------------------------------*
*
*  arraycutpaste.c  -  array: array operations
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
#include <string.h>


/* functions */

static void ArrayCutPasteSub
            (Size dim,
             const Size *srclen,
             const char *srcaddr,
             Size srcsize,
             const Size *boxori,
             const Size *boxlen,
             const Size *boxpos,
             const Size *dstlen,
             char *dstaddr,
             Size dstsize,
             Size elsize)

{
  Size slen, sori;
  Size dlen, dori;
  Size blen, clen, elen;
  const char *saddr;
  char *daddr;

  slen = srclen[dim];
  if ( slen == 0 ) return;
  srcsize /= slen;
  sori = ( boxori == NULL ) ? 0 : boxori[dim] % slen;
  saddr = srcaddr + sori * srcsize * elsize;

  blen = boxlen[dim];
  dlen = dstlen[dim];
  if ( blen > dlen ) blen = dlen;
  if ( blen == 0 ) return;
  dstsize /= dlen;
  dori = ( boxpos == NULL ) ? 0 : boxpos[dim] % dlen;
  daddr = dstaddr + dori * dstsize * elsize;

  if ( dim ) {

    while ( blen-- ) {

      if ( sori == slen ) {
        saddr = srcaddr;
        sori = 0;
      }
      if ( dori == dlen ) {
        daddr = dstaddr;
        dori = 0;
      }

      ArrayCutPasteSub( dim - 1, srclen, saddr, srcsize, boxori, boxlen, boxpos, dstlen, daddr, dstsize, elsize );

      saddr += srcsize * elsize;
      sori++;
      daddr += dstsize * elsize;
      dori++;

    }

  } else {

    while ( blen > 0 ) {

      clen = slen - sori;
      if ( clen > blen ) clen = blen;

      elen = dlen - dori;
      if ( clen > elen ) clen = elen;

      memcpy( daddr, saddr, clen * elsize );

      sori += clen;
      if ( sori == slen ) {
        saddr = srcaddr;
        sori = 0;
      } else {
        saddr += clen * elsize;
      }

      dori += clen;
      if ( dori == dlen ) {
        daddr = dstaddr;
        dori = 0;
      } else {
        daddr += clen * elsize;
      }

      blen -= clen;

    }

  }

}


extern Status ArrayCutPaste
              (Size dim,
               const Size *srclen,
               const void *srcaddr,
               const Size *boxori,
               const Size *boxlen,
               const Size *boxpos,
               const Size *dstlen,
               void *dstaddr,
               Size elsize)

{
  Size srcsize, boxsize, dstsize;
  Status status;

  if ( srclen  == NULL ) return exception( E_ARGVAL );
  if ( srcaddr == NULL ) return exception( E_ARGVAL );
  if ( dstlen  == NULL ) return exception( E_ARGVAL );
  if ( dstaddr == NULL ) return exception( E_ARGVAL );
  if ( elsize  == 0 )    return exception( E_ARGVAL );

  if ( boxlen  == NULL ) boxlen = srclen;

  status = ArraySize( dim, srclen, elsize, &srcsize );
  if ( status ) return exception( status );

  status = ArrayBox( dim, srclen, boxori, boxlen, NULL, &boxsize );
  if ( status ) return exception( status );

  status = ArrayBox( dim, dstlen, boxpos, boxlen, NULL, &boxsize );
  if ( status ) return exception( status );

  status = ArraySize( dim, dstlen, elsize, &dstsize );
  if ( status ) return exception( status );

  if ( boxsize && dstsize ) {
    ArrayCutPasteSub( dim - 1, srclen, srcaddr, srcsize, boxori, boxlen, boxpos, dstlen, dstaddr, dstsize, elsize );
  }

  return status;

}


extern Status ArrayCutPasteClip
              (Size dim,
               const Size *srclen,
               const void *srcaddr,
               const Size *boxori,
               const Size *boxlen,
               const Size *boxpos,
               const Size *dstlen,
               Size *cutlen,
               void *dstaddr,
               Size elsize)

{
  Size srcsize, boxsize, dstsize;
  Status status;

  if ( srclen  == NULL ) return exception( E_ARGVAL );
  if ( srcaddr == NULL ) return exception( E_ARGVAL );
  if ( dstlen  == NULL ) return exception( E_ARGVAL );
  if ( cutlen  == NULL ) return exception( E_ARGVAL );
  if ( dstaddr == NULL ) return exception( E_ARGVAL );
  if ( elsize  == 0 )    return exception( E_ARGVAL );

  if ( boxlen  == NULL ) boxlen = srclen;

  status = ArraySize( dim, srclen, elsize, &srcsize );
  if ( status ) return exception( status );

  status = ArrayBox( dim, srclen, boxori, boxlen, cutlen, &boxsize );
  if ( status && ( status != E_ARRAY_BOUNDS ) ) return exception( status );

  status = ArrayBox( dim, dstlen, boxpos, cutlen, cutlen, &boxsize );
  if ( status && ( status != E_ARRAY_BOUNDS ) ) return exception( status );

  status = ArraySize( dim, dstlen, elsize, &dstsize );
  if ( status ) return exception( status );

  if ( boxsize && dstsize ) {
    ArrayCutPasteSub( dim - 1, srclen, srcaddr, srcsize, boxori, cutlen, boxpos, dstlen, dstaddr, dstsize, elsize );
  }

  return status;

}


extern Status ArrayCutPasteCyc
              (Size dim,
               const Size *srclen,
               const void *srcaddr,
               const Size *boxori,
               const Size *boxlen,
               const Size *boxpos,
               const Size *dstlen,
               void *dstaddr,
               Size elsize)

{
  Size srcsize, boxsize, dstsize;
  Status status;

  if ( srclen  == NULL ) return exception( E_ARGVAL );
  if ( srcaddr == NULL ) return exception( E_ARGVAL );
  if ( dstlen  == NULL ) return exception( E_ARGVAL );
  if ( dstaddr == NULL ) return exception( E_ARGVAL );
  if ( elsize  == 0 )    return exception( E_ARGVAL );

  if ( boxlen  == NULL ) boxlen = srclen;

  status = ArraySize( dim, srclen, elsize, &srcsize );
  if ( status ) return exception( status );

  status = ArraySize( dim, boxlen, elsize, &boxsize );
  if ( status ) return exception( status );

  status = ArraySize( dim, dstlen, elsize, &dstsize );
  if ( status ) return exception( status );

  if ( boxsize && dstsize ) {
    ArrayCutPasteSub( dim - 1, srclen, srcaddr, srcsize, boxori, boxlen, boxpos, dstlen, dstaddr, dstsize, elsize );
  }

  return status;

}
