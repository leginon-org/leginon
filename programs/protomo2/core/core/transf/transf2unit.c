/*----------------------------------------------------------------------------*
*
*  transf2unit.c  -  core: linear transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "transf2.h"


/* functions */

extern Status Transf2Unit
              (Coord A[3][2])

{

  A[0][0] = 1;  A[0][1] = 0;
  A[1][0] = 0;  A[1][1] = 1;
  A[2][0] = 0;  A[2][1] = 0;

  return E_NONE;

}
