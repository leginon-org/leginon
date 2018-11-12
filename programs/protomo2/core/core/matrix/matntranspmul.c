/*----------------------------------------------------------------------------*
*
*  matntranspmul.c  -  matrix operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "matn.h"
#include <string.h>


/* functions */

extern Status MatnTranspMul
              (Size n,
               const Coord *A,
               const Coord *B,
               Coord *C)

{
  Coord Cbuf[n*n];

  Coord *Cij = Cbuf;

  for ( Size i = 0; i < n; i++ ) {

    for ( Size j = 0; j < n; j++ ) {

      const Coord *Aij = A + i;
      const Coord *Bij = B + j;
      Coord cij = 0;
      for ( Size k = 0; k < n; k++ ) {
        cij += *Aij * *Bij;
        Aij += n;
        Bij += n;
      }
      *Cij++ = cij;

    }

  }

  memcpy( C, Cbuf, sizeof(Cbuf) );

  return E_NONE;

}
