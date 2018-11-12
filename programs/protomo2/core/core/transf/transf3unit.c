/*----------------------------------------------------------------------------*
*
*  transf3unit.c  -  core: linear transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "transf3.h"


/* functions */

extern Status Transf3Unit
              (Coord A[4][3])

{

  A[0][0] = 1;  A[0][1] = 0;  A[0][2] = 0;
  A[1][0] = 0;  A[1][1] = 1;  A[1][2] = 0;
  A[2][0] = 0;  A[2][1] = 0;  A[2][2] = 1;
  A[3][0] = 0;  A[3][1] = 0;  A[3][2] = 0;

  return E_NONE;

}
