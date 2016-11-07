/*----------------------------------------------------------------------------*
*
*  matntranspmulvec.c  -  matrix operations
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

extern Status MatnTranspMulVec
              (Size n,
               const Coord *A,
               const Coord *B,
               Coord *C)

{
  Coord Cbuf[n];

  for ( Size i = 0; i < n; i++ ) {

    const Coord *Aij = A + i;
    Coord ci = 0;
    for ( Size j = 0; j < n; j++ ) {
      ci += *Aij * B[j];
      Aij += n;
    }

    Cbuf[i] = ci;

  }

  memcpy( C, Cbuf, sizeof(Cbuf) );

  return E_NONE;

}
