/*----------------------------------------------------------------------------*
*
*  checksum.c  -  core: checksums
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "checksum.h"
#include "exception.h"
#include <string.h>


/* functions */

extern Status Checksum
              (ChecksumType type,
               Size count,
               const void *addr,
               Size sumlen,
               uint8_t *sumaddr)

{

  switch ( type ) {

    case ChecksumTypeXor: ChecksumXor( count, addr, sumlen, sumaddr ); break;

    default: return exception( E_CHECKSUM_TYPE );

  }

  return E_NONE;

}


extern Status ChecksumCalc
              (ChecksumType type,
               Size count,
               const void *addr,
               Size sumlen,
               uint8_t *sumaddr)

{

  switch ( type ) {

    case ChecksumTypeXor: ChecksumXorCalc( count, addr, sumlen, sumaddr ); break;

    default: return exception( E_CHECKSUM_TYPE );

  }

  return E_NONE;

}


extern void ChecksumXor
            (Size count,
             const void *addr,
             Size sumlen,
             uint8_t *sumaddr)

{
  const uint8_t *srcaddr = addr;
  Size i = 0;

  if ( sumlen ) {

    memset( sumaddr, 0, sumlen );

    while ( count-- ) {
      sumaddr[i++] ^= *srcaddr++;
      if ( i >= sumlen ) i = 0;
    }

  }

}


extern void ChecksumXorCalc
            (Size count,
             const void *addr,
             Size sumlen,
             uint8_t *sumaddr)

{
  const uint8_t *srcaddr = addr;
  Size i = 0;

  if ( sumlen ) {

    while ( count-- ) {
      sumaddr[i++] ^= *srcaddr++;
      if ( i >= sumlen ) i = 0;
    }

  }

}
