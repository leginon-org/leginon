/*----------------------------------------------------------------------------*
*
*  arraysize.c  -  array: array operations
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
#include "baselib.h"
#include "exception.h"


/* functions */

extern Status ArraySize
              (Size dim,
               const Size *len,
               Size elsize,
               Size *size)

{
  Size p, s = dim ? elsize : 0;
  Status status = E_NONE;

  while ( dim-- ) {

    status = MulSize( s, *len++, &p );
    if ( status ) return exception( status );
    s = p;

  }

  if ( size != NULL ) {
    *size = elsize ? ( s / elsize ) : 0;
  }

  return status;

}
