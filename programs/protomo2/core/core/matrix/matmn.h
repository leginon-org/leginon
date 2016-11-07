/*----------------------------------------------------------------------------*
*
*  matmn.h  -  core: matrix operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef matmn_h_
#define matmn_h_

#include "matdefs.h"


/* prototypes */

extern Status MatUnit
              (Size m,
               Size n,
               Coord *A);

extern Status MatDiag
              (Size m,
               Size n,
               const Coord *A,
               Coord *B);

extern Status MatTransp
              (Size m,
               Size n,
               const Coord *A,
               Coord *B);

extern Status MatMul
              (Size m,
               Size n,
               Size l,
               const Coord *A,
               const Coord *B,
               Coord *C);

extern Status MatGauss
              (Size m,
               Size n,
               Size l,
               Coord *A,
               Coord *B,
               Size *r);

extern Status MatSvd
              (Size m,
               Size n,
               const Coord *A,
               Coord *U,
               Coord *S,
               Coord *V);


#endif
