/*----------------------------------------------------------------------------*
*
*  mattransp.c  -  matrix operations
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
#include <string.h>


/* functions */

extern Status MatTransp
              (Size m,
               Size n,
               const Coord *A,
               Coord *B)

{
  Coord Bbuf[m*n];

  Coord *Bij = Bbuf;

  for ( Size j = 0; j < n; j++ ) {

    const Coord *Aij = A + j;
    for ( Size i = 0; i < m; i++ ) {
      *Bij++ = *Aij;
      Aij += n;
    }

  }

  memcpy( B, Bbuf, sizeof(Bbuf) );

  return E_NONE;

}
