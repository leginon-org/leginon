/*----------------------------------------------------------------------------*
*
*  mat2inv.c  -  2 x 2 matrix operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "mat2.h"
#include "exception.h"
#include "mathdefs.h"


/* functions */

extern Status Mat2Inv
              (Coord A[2][2],
               Coord B[2][2],
               Coord *det)

#define n 2
#include "matinv.h"
