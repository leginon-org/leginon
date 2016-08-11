/*----------------------------------------------------------------------------*
*
*  mat3inv.c  -  3 x 3 matrix operations
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
#include "exception.h"
#include "mathdefs.h"


/* functions */

extern Status Mat3Inv
              (Coord A[3][3],
               Coord B[3][3],
               Coord *det)

#define n 3
#include "matinv.h"
