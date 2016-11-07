/*----------------------------------------------------------------------------*
*
*  mat3svd.c  -  3 x 3 matrix operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "mat3.h"
#include "matmn.h"


/* functions */

extern Status Mat3Svd
              (Coord A[3][3],
               Coord U[3][3],
               Coord S[3],
               Coord V[3][3])
{

  return MatSvd( 3, 3, (const Coord *)A, (Coord *)U, (Coord *)S, (Coord *)V );

}
