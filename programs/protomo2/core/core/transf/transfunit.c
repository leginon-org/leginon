/*----------------------------------------------------------------------------*
*
*  transfunit.c  -  core: linear transformations: unit matrix
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "transfn.h"


/* functions */

extern Status TransfUnit
              (Size n,
               Coord *A)

{
  Size i, j;

  for ( i = 0; i < n + 1; i++ ) {
    for ( j = 0; j < n; j++ ) {
      *A++ = (i == j) ? 1 : 0;
    }
  }

  return E_NONE;

}
