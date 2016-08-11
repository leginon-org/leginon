/*----------------------------------------------------------------------------*
*
*  transf2diag.c  -  core: linear transformations
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

extern Status Transf2Diag
              (Coord A[2],
               Coord B[3][2])

{

  B[0][0] = A[0];  B[0][1] = 0;
  B[1][0] = 0;     B[1][1] = A[1];
  B[2][0] = 0;     B[2][1] = 0;

  return E_NONE;

}
