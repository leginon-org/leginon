/*----------------------------------------------------------------------------*
*
*  transf2inv.c  -  core: linear transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "transf2.h"
#include "exception.h"
#include "mathdefs.h"


/* functions */

extern Status Transf2Inv
              (Coord A[3][2],
               Coord B[3][2],
               Coord *det)

#define n 2
#include "transfinv.h"
