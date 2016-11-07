/*----------------------------------------------------------------------------*
*
*  matnmul.c  -  matrix operations
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

extern Status MatnMul
              (Size n,
               const Coord *A,
               const Coord *B,
               Coord *C)

{
  Coord Cbuf[n*n];

  const Coord *Ai = A;
  Coord *Cij = Cbuf;

  for ( Size i = 0; i < n; i++ ) {

    for ( Size j = 0; j < n; j++ ) {

      const Coord *Bij = B + j;
      Coord cij = 0;
      for ( Size k = 0; k < n; k++ ) {
        cij += Ai[k] * *Bij;
        Bij += n;
      }
      *Cij++ = cij;

    }

    Ai += n;

  }

  memcpy( C, Cbuf, sizeof(Cbuf) );

  return E_NONE;

}
