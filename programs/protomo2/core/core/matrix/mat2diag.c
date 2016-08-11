/*----------------------------------------------------------------------------*
*
*  mat2diag.c  -  2 x 2 matrix operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "mat2.h"


/* functions */

extern Status Mat2Diag
              (const Coord A[2],
               Coord B[2][2])

{

  B[0][0] = A[0];  B[0][1] = 0;
  B[1][0] = 0;     B[1][1] = A[1];

  return E_NONE;

}
