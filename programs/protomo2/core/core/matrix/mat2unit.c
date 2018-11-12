/*----------------------------------------------------------------------------*
*
*  mat2unit.c  -  2 x 2 matrix operations
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

extern Status Mat2Unit
              (Coord A[2][2])

{

  A[0][0] = 1;  A[0][1] = 0;
  A[1][0] = 0;  A[1][1] = 1;

  return E_NONE;

}
