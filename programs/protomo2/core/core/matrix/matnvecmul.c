/*----------------------------------------------------------------------------*
*
*  matnvecmul.c  -  matrix operations
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

extern Status MatnVecMul
              (Size n,
               const Coord *A,
               const Coord *B,
               Coord *C)

{
  Coord Cbuf[n];

  for ( Size j = 0; j < n; j++ ) {

    const Coord *Bij = B + j;
    Coord cj = 0;
    for ( Size i = 0; i < n; i++ ) {
      cj += A[i] * *Bij;
      Bij += n;
    }
    Cbuf[j] = cj;

  }

  memcpy( C, Cbuf, sizeof(Cbuf) );

  return E_NONE;

}
