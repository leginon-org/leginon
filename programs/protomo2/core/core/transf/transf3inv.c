/*----------------------------------------------------------------------------*
*
*  transf3inv.c  -  core: linear transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "transf3.h"
#include "exception.h"
#include "mathdefs.h"


/* functions */

extern Status Transf3Inv
              (Coord A[4][3],
               Coord B[4][3],
               Coord *det)

#define n 3
#include "transfinv.h"
