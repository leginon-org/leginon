/*----------------------------------------------------------------------------*
*
*  matntransp.c  -  matrix operations
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

extern Status MatnTransp
              (Size n,
               const Coord *A,
               Coord *B)

{
  Coord Bbuf[n*n];

  Coord *Bij = Bbuf;

  for ( Size i = 0; i < n; i++ ) {

    const Coord *Aij = A + i;
    for ( Size j = 0; j < n; j++ ) {
      *Bij++ = *Aij;
      Aij += n;
    }

  }

  memcpy( B, Bbuf, sizeof(Bbuf) );

  return E_NONE;

}
