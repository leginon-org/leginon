/*----------------------------------------------------------------------------*
*
*  transfmul.c  -  core: linear transformations
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
#include "exception.h"
#include <string.h>


/* functions */

extern Status TransfMul
              (Size n,
               const Coord *A,
               const Coord *B,
               Coord *C)

{
  Size p = ( n + 1 ) * n;
  Coord Cbuf[p];

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

  for ( Size j = 0; j < n; j++ ) {

    const Coord *Bij = B + j;
    Coord cij = 0;
    for ( Size k = 0; k < n; k++ ) {
      cij += Ai[k] * *Bij;
      Bij += n;
    }
    *Cij++ = cij + *Bij;

  }

  memcpy( C, Cbuf, p * sizeof(Coord) );

  return E_NONE;

}
