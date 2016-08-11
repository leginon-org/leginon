/*----------------------------------------------------------------------------*
*
*  matdiag.c  -  matrix operations: diagonal matrix
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

extern Status MatDiag
              (Size m,
               Size n,
               const Coord *A,
               Coord *B)

{

  for ( Size i = 0; i < m; i++ ) {
    for ( Size j = 0; j < n; j++ ) {
      *B++ = ( i == j ) ? A[i] : 0;
    }
  }

  return E_NONE;

}
