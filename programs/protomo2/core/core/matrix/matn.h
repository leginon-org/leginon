/*----------------------------------------------------------------------------*
*
*  matn.h  -  core: matrix operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef matn_h_
#define matn_h_

#include "matdefs.h"


/* prototypes */

extern Status MatnUnit
              (Size n,
               Coord *A);

extern Status MatnDiag
              (Size n,
               const Coord *A,
               Coord *B);

extern Status MatnTransp
              (Size n,
               const Coord *A,
               Coord *B);

extern Status MatnInv
              (Size n,
               const Coord *A,
               Coord *B,
               Coord *det);

extern Status MatnMul
              (Size n,
               const Coord *A,
               const Coord *B,
               Coord *C);

extern Status MatnMulTransp
              (Size n,
               const Coord *A,
               const Coord *B,
               Coord *C);

extern Status MatnTranspMul
              (Size n,
               const Coord *A,
               const Coord *B,
               Coord *C);

extern Status MatnMulVec
              (Size n,
               const Coord *A,
               const Coord *B,
               Coord *C);

extern Status MatnTranspMulVec
              (Size n,
               const Coord *A,
               const Coord *B,
               Coord *C);

extern Status MatnVecMul
              (Size n,
               const Coord *A,
               const Coord *B,
               Coord *C);


#endif
