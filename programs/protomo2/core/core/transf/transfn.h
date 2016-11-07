/*----------------------------------------------------------------------------*
*
*  transfn.h  -  core: linear transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef transfn_h_
#define transfn_h_

#include "transfdefs.h"


/* prototypes */

extern Status TransfUnit
              (Size n,
               Coord *A);

extern Status TransfDiag
              (Size n,
               const Coord *A,
               Coord *B);

extern Status TransfTransl
              (Size n,
               const Coord *A,
               Coord *B);

extern Status TransfInv
              (Size n,
               const Coord *A,
               Coord *B,
               Coord *det);

extern Status TransfMul
              (Size n,
               const Coord *A,
               const Coord *B,
               Coord *C);

extern Status TransfTranspMulVec
              (Size n,
               const Coord *A,
               const Coord *B,
               Coord *C);


#endif
