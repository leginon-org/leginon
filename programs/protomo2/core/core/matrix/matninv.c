/*----------------------------------------------------------------------------*
*
*  matninv.c  -  matrix operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "matn.h"
#include "exception.h"
#include "mathdefs.h"


/* functions */

extern Status MatnInv
              (Size n,
               const Coord *A,
               Coord *B,
               Coord *det)

#include "matinv.h"
