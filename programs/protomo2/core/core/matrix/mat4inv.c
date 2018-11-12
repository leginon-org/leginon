/*----------------------------------------------------------------------------*
*
*  mat4inv.c  -  4 x 4 matrix operations
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
#include "exception.h"
#include "mathdefs.h"


/* functions */

extern Status Mat4Inv
              (Coord A[4][4],
               Coord B[4][4],
               Coord *det)

#define n 4
#include "matinv.h"
