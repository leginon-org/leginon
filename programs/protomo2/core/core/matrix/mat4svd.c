/*----------------------------------------------------------------------------*
*
*  mat4svd.c  -  4 x 4 matrix operations
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
#include "matmn.h"


/* functions */

extern Status Mat4Svd
              (Coord A[4][4],
               Coord U[4][4],
               Coord S[4],
               Coord V[4][4])
{

  return MatSvd( 4, 4, (const Coord *)A, (Coord *)U, (Coord *)S, (Coord *)V );

}
