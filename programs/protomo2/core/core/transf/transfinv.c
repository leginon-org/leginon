/*----------------------------------------------------------------------------*
*
*  transfinv.c  -  core: linear transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "transfn.h"
#include "exception.h"
#include "mathdefs.h"


/* functions */

extern Status TransfInv
              (Size n,
               const Coord *A,
               Coord *B,
               Coord *det)

#include "transfinv.h"
