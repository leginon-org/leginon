/*----------------------------------------------------------------------------*
*
*  transf2.h  -  core: linear transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef transf2_h_
#define transf2_h_

#include "transfdefs.h"


/* prototypes */

extern Status Transf2Unit
              (Coord A[3][2]);

extern Status Transf2Diag
              (Coord A[2],
               Coord B[3][2]);

extern Status Transf2Transl
              (Coord A[2],
               Coord B[3][2]);

extern Status Transf2Inv
              (Coord A[3][2],
               Coord B[3][2],
               Coord *det);

extern Status Transf2Mul
              (Coord A[3][2],
               Coord B[3][2],
               Coord C[3][2]);

extern Status Transf2TranspMulVec
              (Coord A[3][2],
               Coord B[2],
               Coord C[2]);


#endif
