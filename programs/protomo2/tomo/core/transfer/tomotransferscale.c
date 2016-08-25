/*----------------------------------------------------------------------------*
*
*  tomotransferscale.c  -  tomography: transfer functions
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomotransfer.h"
#include "exception.h"


/* functions */

extern void TomotransferScale
            (Coord A[3][3],
             Coord sampling,
             const Size len[3],
             Coord B[3][3])

{
  Coord s0 = 1 / ( sampling * len[0] );
  Coord s1 = 1 / ( sampling * len[1] );
  Coord s2 = 1 / ( sampling * len[2] );

  B[0][0] = A[0][0] * s0; B[0][1] = A[0][1] * s1; B[0][2] = A[0][2] * s2;
  B[1][0] = A[1][0] * s0; B[1][1] = A[1][1] * s1; B[1][2] = A[1][2] * s2;
  B[2][0] = A[2][0] * s0; B[2][1] = A[2][1] * s1; B[2][2] = A[2][2] * s2;

}
