/*----------------------------------------------------------------------------*
*
*  transf3.h  -  core: linear transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef transf3_h_
#define transf3_h_

#include "transfdefs.h"


/* prototypes */

extern Status Transf3Unit
              (Coord A[4][3]);

extern Status Transf3Diag
              (Coord A[3],
               Coord B[4][3]);

extern Status Transf3Transl
              (Coord A[3],
               Coord B[4][3]);

extern Status Transf3Inv
              (Coord A[4][3],
               Coord B[4][3],
               Coord *det);

extern Status Transf3Mul
              (Coord A[4][3],
               Coord B[4][3],
               Coord C[4][3]);

extern Status Transf3TranspMulVec
              (Coord A[4][3],
               Coord B[3],
               Coord C[3]);


#endif
