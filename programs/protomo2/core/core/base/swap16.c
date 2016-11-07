/*----------------------------------------------------------------------------*
*
*  swap16.c  -  core: swap bytes
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "baselib.h"


/* functions */

extern void Swap16
            (Size size,
             const void *src,
             void *dst)

{
  const uint8_t *s = src;
  uint8_t *d = dst;

  while ( size-- ) {
    uint8_t v0 = *s++;
    uint8_t v1 = *s++;
    *d++ = v1;
    *d++ = v0;
  }

}
