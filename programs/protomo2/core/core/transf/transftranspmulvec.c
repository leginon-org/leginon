/*----------------------------------------------------------------------------*
*
*  transftranspmulvec.c  -  core: linear transformations
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

extern Status TransfTranspMulVec
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
    Cbuf[i] = ci + *Aij;

  }

  memcpy( C, Cbuf, n * sizeof(Coord) );

  return E_NONE;

}
