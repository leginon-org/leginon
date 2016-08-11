/*----------------------------------------------------------------------------*
*
*  mat4unit.c  -  4 x 4 matrix operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "mat4.h"


/* functions */

extern Status Mat4Unit
              (Coord A[4][4])

{

  A[0][0] = 1;  A[0][1] = 0;  A[0][2] = 0;  A[0][3] = 0;
  A[1][0] = 0;  A[1][1] = 1;  A[1][2] = 0;  A[1][3] = 0;
  A[2][0] = 0;  A[2][1] = 0;  A[2][2] = 1;  A[2][3] = 0;
  A[3][0] = 0;  A[3][1] = 0;  A[3][2] = 0;  A[3][3] = 1;

  return E_NONE;

}
