/*----------------------------------------------------------------------------*
*
*  arrayfill.c  -  array: array operations
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

extern Status ArrayFill
              (Size dim,
               const void *srcaddr,
               const Size *dstlen,
               void *dstaddr,
               Size elsize)

{
  Size size;
  Status status;

  status = ArraySize( dim, dstlen, elsize, &size );
  if ( status ) return exception( status );

  if ( size && ( elsize > 0 ) ) {

    char *end = dstaddr;
    memcpy( end, srcaddr, elsize );
    end += elsize; size--;
    Size count = 1;

    while ( size ) {

      Size copy = ( size < count ) ? size : count;
      memcpy( end, dstaddr, copy * elsize );
      end += copy * elsize; size -= copy;
      count += copy;

    }

  }

  return status;

}
