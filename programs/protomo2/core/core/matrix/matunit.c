/*----------------------------------------------------------------------------*
*
*  matunit.c  -  matrix operations: unit matrix
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "matmn.h"


/* functions */

extern Status MatUnit
              (Size m,
               Size n,
               Coord *A)

{

  for ( Size i = 0; i < m; i++ ) {
    for ( Size j = 0; j < n; j++ ) {
      *A++ = ( i == j ) ? 1 : 0;
    }
  }

  return E_NONE;

}
