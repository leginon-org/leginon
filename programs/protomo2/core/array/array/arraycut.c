/*----------------------------------------------------------------------------*
*
*  arraycut.c  -  array: array operations
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

static void ArrayCutSub
            (Size dim,
             const Size *srclen,
             const char *srcaddr,
             Size srcsize,
             const Size *boxori,
             const Size *boxlen,
             char **dstaddr,
             Size elsize)

{
  Size slen, sori;
  Size dlen, clen;
  const char *saddr;

  slen = srclen[dim];
  if ( slen == 0 ) return;
  srcsize /= slen;
  sori = ( boxori == NULL ) ? 0 : boxori[dim] % slen;
  saddr = srcaddr + sori * srcsize * elsize;

  dlen = boxlen[dim];

  if ( dim ) {

    while ( dlen-- ) {

      if ( sori == slen ) {
        saddr = srcaddr;
        sori = 0;
      }

      ArrayCutSub( dim - 1, srclen, saddr, srcsize, boxori, boxlen, dstaddr, elsize );

      saddr += srcsize * elsize;
      sori++;

    }

  } else {

    clen = slen - sori;

    while ( dlen > 0 ) {

      if ( clen > dlen ) clen = dlen;
      memcpy( *dstaddr, saddr, clen * elsize );

      dlen -= clen;
      *dstaddr += clen * elsize;

      saddr = srcaddr;
      clen = slen;

    }

  }

}


extern Status ArrayCut
              (Size dim,
               const Size *srclen,
               const void *srcaddr,
               const Size *boxori,
               const Size *boxlen,
               void *dstaddr,
               Size elsize)

{
  Size srcsize, boxsize;
  char *daddr = dstaddr;
  Status status;

  if ( srclen  == NULL ) return exception( E_ARGVAL );
  if ( srcaddr == NULL ) return exception( E_ARGVAL );
  if ( boxlen  == NULL ) return exception( E_ARGVAL );
  if ( dstaddr == NULL ) return exception( E_ARGVAL );
  if ( elsize  == 0 )    return exception( E_ARGVAL );

  status = ArraySize( dim, srclen, elsize, &srcsize );
  if ( status ) return exception( status );

  status = ArrayBox( dim, srclen, boxori, boxlen, NULL, &boxsize );
  if ( status ) return exception( status );

  if ( boxsize ) {
    ArrayCutSub( dim - 1, srclen, srcaddr, srcsize, boxori, boxlen, &daddr, elsize );
  }

  return status;

}


extern Status ArrayCutClip
              (Size dim,
               const Size *srclen,
               const void *srcaddr,
               const Size *boxori,
               const Size *boxlen,
               Size *dstlen,
               void *dstaddr,
               Size elsize)

{
  Size srcsize, boxsize;
  char *daddr = dstaddr;
  Status status;

  if ( srclen  == NULL ) return exception( E_ARGVAL );
  if ( srcaddr == NULL ) return exception( E_ARGVAL );
  if ( boxlen  == NULL ) return exception( E_ARGVAL );
  if ( dstlen  == NULL ) return exception( E_ARGVAL );
  if ( dstaddr == NULL ) return exception( E_ARGVAL );
  if ( elsize  == 0 )    return exception( E_ARGVAL );

  status = ArraySize( dim, srclen, elsize, &srcsize );
  if ( status ) return exception( status );

  status = ArrayBox( dim, srclen, boxori, boxlen, dstlen, &boxsize );
  if ( status && ( status != E_ARRAY_BOUNDS ) ) return exception( status );

  if ( boxsize ) {
    ArrayCutSub( dim - 1, srclen, srcaddr, srcsize, boxori, dstlen, &daddr, elsize );
  }

  return status;

}


extern Status ArrayCutCyc
              (Size dim,
               const Size *srclen,
               const void *srcaddr,
               const Size *boxori,
               const Size *boxlen,
               void *dstaddr,
               Size elsize)

{
  Size srcsize, boxsize;
  char *daddr = dstaddr;
  Status status;

  if ( srclen  == NULL ) return exception( E_ARGVAL );
  if ( srcaddr == NULL ) return exception( E_ARGVAL );
  if ( boxlen  == NULL ) return exception( E_ARGVAL );
  if ( dstaddr == NULL ) return exception( E_ARGVAL );
  if ( elsize  == 0 )    return exception( E_ARGVAL );

  status = ArraySize( dim, srclen, elsize, &srcsize );
  if ( status ) return exception( status );

  status = ArraySize( dim, boxlen, elsize, &boxsize );
  if ( status ) return exception( status );

  if ( boxsize ) {
    ArrayCutSub( dim - 1, srclen, srcaddr, srcsize, boxori, boxlen, &daddr, elsize );
  }

  return status;

}
